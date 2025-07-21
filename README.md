# Iterative Feedback Entity and Relation Extraction and Integration for Medicinal Plants based on LLMs

This project leverages Large Language Models (LLMs) to automatically extract, integrate, and standardize entities and relations from medicinal plant texts, facilitating structured knowledge organization and intelligent analysis in Traditional Chinese Medicine (TCM).

## Data Sources

The dataset contains 265 samples, derived from multiple authoritative sources:

- Medicinal Plant Images Database by the School of Chinese Medicine, Hong Kong Baptist University  
  [http://library.hkbu.edu.hk/electronic/libdbs/mpd/](http://library.hkbu.edu.hk/electronic/libdbs/mpd/)
- Pharmacopoeia of the People’s Republic of China (2020 Edition)  
  [https://ydz.chp.org.cn/](https://ydz.chp.org.cn/)
- TCMID Database  
  [http://bidd.group/TCMID/](http://bidd.group/TCMID/)

## Data Format

### Raw Data

Raw data is stored as `.txt` files in the `data/` directory, each file corresponding to a medicinal plant. Example content:

```
地笋【科属归类】唇形科地笋属【药用部位】以根茎部份入药。中药名:地笋。【应用举例】治黄疸:泽兰根、赤小豆各60克，水煎当茶饮。(沙漠地区药用植物)
```

### Entity and Relation Types

- `entity_types.txt`: Defines extractable entity types (e.g., Genus, Disease, Family, Medicinal Material, Medicinal Plant, Medicinal Part, etc.)
- `relation_types.txt`: Defines extractable relation types (e.g., Contains, Belongs to Genus, Belongs to Family, Treats, Medicinal Material, Medicinal Part, etc.)

## Main Features

- **Entity & Relation Extraction**: Automatically identifies medicinal plant-related entities and their semantic relations using LLMs.
- **Type Integration & Standardization**: Iteratively normalizes entity and relation types to improve consistency and accuracy.
- **Result Output**: Supports structured JSON output and Excel export for further analysis.

## Usage

### 1. Install Dependencies

Ensure Python 3.7+ is installed. Install required packages (e.g., `openai`, `sympy`, etc.) as needed.

### 2. Configure OpenAI API Key

Edit `config.py` to set your OpenAI API key and base URL:

```python
API_CONFIG = {
    'openai': {
        'api_key': 'YOUR_OPENAI_API_KEY',
        'base_url': 'https://api.openai.com/v1'  # or your proxy URL
    }
}
```
You can also set the `OPENAI_API_KEY` environment variable.

### 3. Run the Main Program

Edit the `CONFIG` dictionary in `main.py` to specify input/output directories, processing range, and other parameters. Key parameters:

- `input_dir`: Directory of raw text data (e.g., `data/`)
- `entity_file`: Entity type definition file (e.g., `entity_types.txt`)
- `relation_file`: Relation type definition file (e.g., `relation_types.txt`)
- `output_dir`: Output directory for extraction results (e.g., `output_results/`)
- `start_index`/`end_index`: Index range of files to process
- `mode`: Processing mode (`normal` for standard, `strict` for using only converged types)
- `disable_validation`: Whether to disable type integration and validation

Example command:

```bash
python main.py
```

### 4. Output

- Structured extraction results are saved in the `output_results/` directory as JSON files.
- Logs are saved in the `logs/` directory.
- Optional Excel summary files are saved in the `excel_outputs/` directory.

## Example Output

The extracted JSON output format:

```json
{
  "entities": [
    {"entity": "地笋", "type": "药用植物"},
    {"entity": "唇形科", "type": "科"},
    {"entity": "地笋属", "type": "属"},
    {"entity": "根茎部份", "type": "药用部位"},
    {"entity": "黄疸", "type": "疾病"}
  ],
  "relationships": [
    {"head": "地笋", "predicate": "属于科", "tail": "唇形科"},
    {"head": "地笋", "predicate": "属于属", "tail": "地笋属"},
    {"head": "地笋", "predicate": "药用部位", "tail": "根茎部份"},
    {"head": "地笋", "predicate": "治疗", "tail": "黄疸"}
  ]
}
```

## Acknowledgements

This project acknowledges the following databases and literature for their open access and support:

- Medicinal Plant Images Database, School of Chinese Medicine, Hong Kong Baptist University
- Pharmacopoeia of the People’s Republic of China (2020 Edition)
- TCMID Database

---

For further help or questions, please contact the project maintainer. 