import argparse
import os
from abc import ABC, abstractmethod
from collections import Counter
from typing import Dict, Optional, List
import sys
import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('text_sanitizer')

class ConfigLoader:
    
    @staticmethod
    def load_from_cli() -> Dict:
        parser = argparse.ArgumentParser(description='Text Sanitizer')
        parser.add_argument('--source', help='Source file path or "sample" for sample data')
        parser.add_argument('--target', help='Target file path (optional)')
        parser.add_argument('--config', help='Path to config file (optional)')
        
        args = parser.parse_args()
        
        if args.config:
            return ConfigLoader.load_from_file(args.config)

        return vars(args)
    
    @staticmethod
    def load_from_file(config_path: str) -> Dict:
        try:
            with open(config_path, 'r') as file:
                config = json.load(file)
                logger.info(f"Loaded configuration from {config_path}")
                return config
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            return {}

    @staticmethod
    def get_config() -> Dict:
        """Get configuration from available sources"""
        config = ConfigLoader.load_from_cli()
        
        if not config.get('source'):
            logger.info("No source provided, using sample data")
            config['source'] = 'sample'
        
        return config


class InputReader(ABC):
    
    @abstractmethod
    def read(self) -> str:
        pass
    
    @staticmethod
    def create(source: str) -> 'InputReader':
        if source == 'sample':
            return SampleDataReader()
        elif os.path.isfile(source):
            return FileReader(source)
        else:
            logger.warning(f"Source '{source}' is not recognized as a file. Treating as raw text.")
            return StringReader(source)


class OutputWriter(ABC):
    
    @abstractmethod
    def write(self, sanitized_text: str, statistics: Dict) -> None:
        pass
    
    @staticmethod
    def create(target: Optional[str]) -> 'OutputWriter':
        if not target:
            return ConsoleWriter()
        else:
            return FileWriter(target)


class TextSanitizer(ABC):
    
    @abstractmethod
    def sanitize(self, text: str) -> str:
        pass


class StatisticsGenerator(ABC):
    
    @abstractmethod
    def generate(self, text: str) -> Dict:
        pass


class FileReader(InputReader):
    
    def __init__(self, source_path: str):
        self.source_path = source_path
    
    def read(self) -> str:
        try:
            with open(self.source_path, 'r', encoding='utf-8') as file:
                content = file.read()
                logger.info(f"Read {len(content)} characters from {self.source_path}")
                return content
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return ""


class StringReader(InputReader):
    
    def __init__(self, text: str):
        self.text = text
    
    def read(self) -> str:
        return self.text


class SampleDataReader(InputReader):
    
    def read(self) -> str:
        sample_data = [
            "This is a SAMPLE text with MIXED case.",
            "It contains\ttabs\tand\tspaces.",
            "Some numbers 123 and special ch@r@cters!",
            "",  # Empty line
            "Another line with\tmore\ttabs.",
            "THE END OF THE SAMPLE."
        ]
        
        corrupted_data = [
            None, 
            "\t\t\tMultiple tabs at the beginning",
            "Line with unicode: € £ ¥ § ツ",
            "Line with very long text " + "a" * 100
        ]
        
        all_data = sample_data + [line for line in corrupted_data if line is not None]
        sample_text = "\n".join(all_data)
        
        logger.info(f"Generated sample data with {len(sample_text)} characters")
        return sample_text


class ConsoleWriter(OutputWriter):
    
    def write(self, sanitized_text: str, statistics: Dict) -> None:
        print("\n" + "="*50)
        print("SANITIZED TEXT:")
        print("="*50)
        print(sanitized_text)
        
        print("\n" + "="*50)
        print("STATISTICS:")
        print("="*50)
        
        print("\nCharacter Frequencies:")
        for key, value in statistics.items():
            if key == "total_characters":
                continue
            print(f"  '{key}': {value}")
        
        if "total_characters" in statistics:
            print(f"\nTotal characters: {statistics['total_characters']}")
        
        logger.info("Output written to console")


class FileWriter(OutputWriter):
    
    def __init__(self, target_path: str):
        self.target_path = target_path
    
    def write(self, sanitized_text: str, statistics: Dict) -> None:
        try:
            with open(self.target_path, 'w', encoding='utf-8') as file:
                file.write("="*50 + "\n")
                file.write("SANITIZED TEXT:\n")
                file.write("="*50 + "\n")
                file.write(sanitized_text)
                
                file.write("\n\n" + "="*50 + "\n")
                file.write("STATISTICS:\n")
                file.write("="*50 + "\n\n")
                
                file.write("Character Frequencies:\n")
                for key, value in statistics.items():
                    if key == "total_characters":
                        continue
                    file.write(f"  '{key}': {value}\n")
                
                if "total_characters" in statistics:
                    file.write(f"\nTotal characters: {statistics['total_characters']}\n")
            
            print(f"Output written to {self.target_path}")
            logger.info(f"Output written to file: {self.target_path}")
        except Exception as e:
            logger.error(f"Error writing to file: {e}")
            print(f"Error writing to file: {e}")


class BasicSanitizer(TextSanitizer):
    
    def sanitize(self, text: str) -> str:
        if not text:
            logger.warning("Empty text received for sanitization")
            return ""
        
        if text is None:
            logger.warning("None value received for sanitization")
            return ""
        
        try:
            text = text.lower()
            text = text.replace('\t', '____')
            
            logger.info("Text sanitization completed successfully")
            return text
        except Exception as e:
            logger.error(f"Error during text sanitization: {e}")
            return ""


class AlphabetCounter(StatisticsGenerator):
    
    def generate(self, text: str) -> Dict:
        if not text:
            logger.warning("Empty text received for statistics generation")
            return {"total_characters": 0}
        
        try:
            char_counts = Counter(text)
            alphabet_counts = {char: count for char, count in char_counts.items() if char.isalpha()}
            alphabet_counts["total_characters"] = len(text)
            
            result = dict(sorted(alphabet_counts.items()))
            
            logger.info(f"Generated statistics for {len(text)} characters")
            return result
        except Exception as e:
            logger.error(f"Error generating statistics: {e}")
            return {"total_characters": 0}


class EnhancedStatisticsGenerator(StatisticsGenerator):
    
    def generate(self, text: str) -> Dict:
        if not text:
            logger.warning("Empty text received for statistics generation")
            return {"total_characters": 0}
        
        try:
            basic_stats = AlphabetCounter().generate(text)
            stats = {}
            
            stats["alphabetic_chars"] = sum(1 for c in text if c.isalpha())
            stats["numeric_chars"] = sum(1 for c in text if c.isdigit())
            stats["whitespace_chars"] = sum(1 for c in text if c.isspace())
            stats["special_chars"] = len(text) - stats["alphabetic_chars"] - stats["numeric_chars"] - stats["whitespace_chars"]
            
            words = [w for w in text.split() if w]
            stats["total_words"] = len(words)
            stats["avg_word_length"] = round(sum(len(w) for w in words) / len(words) if words else 0, 2)
            
            lines = text.split('\n')
            stats["total_lines"] = len(lines)
            stats["non_empty_lines"] = sum(1 for line in lines if line.strip())
            
            result = {**basic_stats, **stats}
            
            logger.info(f"Generated enhanced statistics for {len(text)} characters")
            return result
        except Exception as e:
            logger.error(f"Error generating enhanced statistics: {e}")
            return {"total_characters": 0, "error": str(e)}


class TextProcessor:
    
    def __init__(self, reader: InputReader, writer: OutputWriter, 
                 sanitizer: TextSanitizer, stats_generator: StatisticsGenerator):
        self.reader = reader
        self.writer = writer
        self.sanitizer = sanitizer
        self.stats_generator = stats_generator
    
    def process(self):
        try:
            logger.info("Reading input text")
            input_text = self.reader.read()
            
            logger.info("Sanitizing text")
            sanitized_text = self.sanitizer.sanitize(input_text)
            
            logger.info("Generating statistics")
            statistics = self.stats_generator.generate(sanitized_text)
            
            logger.info("Writing output")
            self.writer.write(sanitized_text, statistics)
            
            return True
        except Exception as e:
            logger.error(f"Error during text processing: {e}")
            print(f"An error occurred: {e}")
            return False


def main():
    try:
        config = ConfigLoader.get_config()
        
        reader = InputReader.create(config.get('source', 'sample'))
        writer = OutputWriter.create(config.get('target'))
        sanitizer = BasicSanitizer()

        use_enhanced_stats = True 
        stats_generator = EnhancedStatisticsGenerator() if use_enhanced_stats else AlphabetCounter()

        processor = TextProcessor(reader, writer, sanitizer, stats_generator)
        success = processor.process()
        
        if success:
            logger.info("Text processing completed successfully")
        else:
            logger.error("Text processing failed")
            sys.exit(1)
    
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        print(f"Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
