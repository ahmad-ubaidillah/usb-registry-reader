import argparse
import struct
import os
import json
from datetime import datetime
from Registry import Registry
from typing import Dict, List, Union

class RegistryHiveAnalyzer:
    def __init__(self):
        self.results: List[Dict] = []
        self._key_count = 0

    def _format_value(self, value) -> Union[str, int, bytes]:
        """Convert registry value to appropriate Python type"""
        try:
            if value.value_type_str() == 'REG_BINARY':
                return value.value().hex()
            if value.value_type_str() == 'REG_DWORD':
                return struct.unpack('<I', value.value())[0]
            return str(value.value())
        except Exception as e:
            return f"[ERROR: {str(e)}]"

    def _process_recent_docs(self, key) -> List[str]:
        """Parse MRUListEx structure with error handling"""
        try:
            mru_data = next((v for v in key.values() if v.name() == "MRUListEx"), None)
            if not mru_data:
                return []

            mru_order = [i[0] for i in struct.iter_unpack("<I", mru_data.value()) 
                        if i[0] != 0xFFFFFFFF]
            
            return [
                f"{idx}. {self._decode_utf16le(v.value())}"
                for idx in mru_order
                if (v := next((val for val in key.values() if val.name() == str(idx)), None))
            ]
        except Exception as e:
            return [f"Error parsing RecentDocs: {str(e)}"]

    def _decode_utf16le(self, data: bytes) -> str:
        """Safely decode UTF-16LE strings"""
        return data.decode('utf-16-le', errors='ignore').split('\x00')[0]

    def analyze(self, file_path: str, verbose: bool = False) -> None:
        """Main analysis workflow"""
        try:
            reg = Registry.Registry(file_path)
            self._traverse_keys(reg.root(), verbose)
        except Exception as e:
            print(f"Analysis failed: {str(e)}")

    def _traverse_keys(self, key, verbose: bool) -> None:
        """Recursive key traversal with progress feedback"""
        self._key_count += 1
        if verbose and self._key_count % 1000 == 0:
            print(f"Processed {self._key_count} keys...")

        entry = {
            'path': key.path(),
            'timestamp': key.timestamp().isoformat(),
            'values': {
                val.name() or "(Default)": self._format_value(val)
                for val in key.values()
            }
        }

        if "RecentDocs" in key.path():
            entry['recent_docs'] = self._process_recent_docs(key)

        self.results.append(entry)

        for subkey in key.subkeys():
            self._traverse_keys(subkey, verbose)

    def save_report(self, format: str = 'text', output_file: str = 'output') -> None:
        """Save results in specified format"""
        {
            'text': self._save_text,
            'json': self._save_json
        }[format](output_file)

    def _save_text(self, filename: str) -> None:
        """Generate human-readable text report"""
        with open(f"{filename}.txt", 'w', encoding='utf-8') as f:
            for entry in self.results:
                f.write(f"\n[Key] {entry['path']} ({entry['timestamp']})\n")
                for name, value in entry['values'].items():
                    f.write(f"  {name}: {value}\n")
                if 'recent_docs' in entry:
                    f.write("\n  Recent Documents:\n")
                    f.write("\n".join(f"    {doc}" for doc in entry['recent_docs']))

    def _save_json(self, filename: str) -> None:
        """Generate machine-readable JSON output"""
        with open(f"{filename}.json", 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)

def main():
    parser = argparse.ArgumentParser(
        description="Registry Hive Analyzer - Simple yet powerful registry parser",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('file', help="Path to registry hive file (.hiv, .dat)")
    parser.add_argument('-o', '--output', help="Output file name (without extension)", default="output")
    parser.add_argument('-f', '--format', choices=['text', 'json'], default='text',
                      help="Output format")
    parser.add_argument('-v', '--verbose', action='store_true',
                      help="Show processing progress")

    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found")
        exit(1)

    analyzer = RegistryHiveAnalyzer()
    analyzer.analyze(args.file, args.verbose)
    analyzer.save_report(args.format, args.output)
    
    print(f"\nAnalysis complete! Results saved to {args.output}.{args.format}")

if __name__ == "__main__":
    main()
