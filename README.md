# 3D Printing Services Platform

A comprehensive AI-powered 3D printing platform featuring automatic model generation and professional printing services.

## Features

### Homepage
- Service overview and selection
- Professional landing page design
- Easy navigation to services

### AI 3D Model Generation
- AI-powered 3D model generation from text descriptions
- Multi-image upload support for reference
- Interactive 3D preview with Plotly
- Real-time model refinement
- STL export for 3D printing
- Python/trimesh code generation

### Professional Print Service
- STL file upload
- AI-powered material recommendation based on use case
- Automatic Bambu Studio CLI configuration
- Cost estimation
- Print parameter optimization
- Order management

## How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file with the keys for whichever provider(s) you want to use:
```
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```
The AI generation page lets you switch between providers at runtime. At least one key must be set.

### 3. Run the Application
```bash
streamlit run Home.py
```

The app will open in your browser at `http://localhost:8501`

### 4. Log In

Every page is gated by a login screen. Use the following demo credentials:

| Field | Value |
| --- | --- |
| **Username** | `tester` |
| **Password** | `Test123.` |

Sessions persist while the browser tab is open and reset when it is closed. The credentials are defined in [`auth.py`](auth.py) — change `_USERNAME` and `_PASSWORD_HASH` (a SHA-256 hash of the new password) before deploying anywhere public.

## Project Structure

```
Thesis-3D-printing/
├── Home.py                          # Homepage and entry point
├── auth.py                          # Login gate (username / SHA-256 password)
├── pages/
│   ├── 1_AI_3D_Generation.py       # AI model generation service
│   ├── 2_Print_With_Us.py          # 3D printing service
│   └── 3_Pricing.py                # Pricing page (coming soon)
├── api_handler_simple.py            # OpenAI + Gemini API integration
├── print_operator_cli.py            # CLI tool for processing orders (for you)
├── orders/                          # Auto-generated order storage
│   └── order_XXXXXX/               # Each order gets its own directory
│       ├── model.stl               # Customer's STL file
│       ├── order_XXXXXX_summary.txt # Order summary with CLI command
│       └── order_XXXXXX_data.json  # Machine-readable order data
├── requirements.txt                 # Python dependencies
├── .env                            # API configuration (create this)
└── .gitignore                      # Prevents orders from being committed
```

## Workflow

### AI 3D Generation Workflow
1. **Create**: Describe your model or upload reference images
2. **Preview**: View interactive 3D preview and make refinements
3. **Export**: Download Python code and STL file

### Print Service Workflow
1. **Upload**: Customer uploads STL file and describes use case
2. **Analysis**: AI recommends material and print settings
3. **Order Submission**: Customer submits order with all details
4. **Print Operator (You)**: Receives order and uses CLI to slice with recommended settings
5. **Production**: Print and ship to customer

## Technologies

- **Frontend**: Streamlit
- **AI**: OpenAI GPT-5-mini / GPT-4o-mini (via Responses API with fallback to Chat Completions) and Google Gemini 3.1 Pro (via `google-genai` with fallback to `google-generativeai`)
- **CAD**: CadQuery (parametric, phase-driven code generation)
- **RAG**: Local retrieval over Bambu filament datasheets for material recommendations
- **3D Processing**: trimesh, numpy
- **Visualization**: Plotly
- **Slicing**: Bambu Studio CLI (configured automatically)

## Features in Detail

### AI Model Generation
- Text-to-3D using AI-generated Python/trimesh code
- Vision API support for image-based generation
- Interactive parameter tuning
- Automatic code error detection and fixing
- Real-time 3D visualization

### Print Service
- Use case analysis for optimal material selection
- Automatic print parameter configuration
- Bambu Studio CLI integration
- Cost estimation based on volume and material
- Priority ordering (Standard/Rush/Economy)

## Requirements

- Python 3.8+
- An OpenAI API key and/or a Google Gemini API key (at least one is required for AI features; the UI lets you pick which provider to use)
- Bambu Studio CLI (for actual slicing, optional for demo)

### Installation

1. **Download Bambu Studio**:
   - Visit [Bambu Lab Official Site](https://bambulab.com/en/download/studio)
   - Download the appropriate version for your OS
   - Install Bambu Studio

2. **Locate CLI Tool**:
   - **Windows**: `C:\Program Files\BambuStudio\bambu-cli.exe`
   - **macOS**: `/Applications/BambuStudio.app/Contents/MacOS/bambu-cli`
   - **Linux**: `/usr/bin/bambu-cli`

3. **Add to PATH** (Optional):
   ```bash
   # Windows (PowerShell)
   $env:Path += ";C:\Program Files\BambuStudio"
   
   # macOS/Linux
   export PATH=$PATH:/Applications/BambuStudio.app/Contents/MacOS
   ```

### Usage

The Print Service automatically:
- ✅ Detects if Bambu Studio CLI is installed
- ✅ Generates optimal slicing parameters based on AI recommendations
- ✅ Executes CLI commands with proper configuration
- ✅ Provides simulation mode if CLI is not available
- ✅ Supports custom CLI paths
- ✅ Offers both command-line and JSON configuration modes

### CLI Configuration Options

**In the Print Service page:**
1. Upload your STL file
2. Provide use case description
3. Review AI recommendations
4. Navigate to "Advanced CLI Settings" for:
   - Custom CLI path specification
   - JSON configuration mode
   - Command preview

### Simulation Mode

If Bambu Studio CLI is not installed:
- ✅ Simulation mode automatically enabled
- ✅ Complete workflow demonstration
- ✅ No external dependencies required
- ✅ Perfect for testing and demos

### CLI Command Example

```bash
# Automatically generated command:
bambu-cli slice input.stl -o output.3mf \
  --filament-type PLA \
  --layer-height 0.2 \
  --infill-density 20% \
  --wall-loops 3 \
  --support-material
```

### JSON Configuration Mode

```json
{
  "input": "model.stl",
  "output": "sliced_model.3mf",
  "print_settings": {
    "layer_height": 0.2,
    "infill_density": 20,
    "perimeters": 3,
    "support_material": true
  },
  "filament_settings": {
    "filament_type": "PLA"
  }
}
```

## Notes

- The AI generation service works in demo mode without an API key
- The print service provides AI recommendations when an OpenAI or Gemini API key is configured
- STL files can be transferred seamlessly between services
- All generated models are automatically optimized for 3D printing
- Bambu Studio CLI integration supports both real slicing and simulation
- Custom CLI paths can be configured in Advanced Settings

## Support

For issues or questions, please check the documentation in each page or contact support.
