# AI-Powered Product-Level BCG Matrix Generator

An **AI-powered strategic analysis tool** that automatically generates a **Product-Level BCG Matrix** for any company using a LLM.

The system identifies major products or business units of a company, evaluates **market growth** and **relative market share**, classifies them into **BCG quadrants**, and visualizes the results in a **professional BCG matrix chart**. This tool is useful for **strategy analysis, business consulting, and market research.**

# Features

• Automated **product-level BCG analysis** using AI

• Identification of **major products/business units**

• Classification into **BCG quadrants**: Star, Cash Cow, Question Mark and Dog

• **Confidence scoring** for each product classification

• **Interactive BCG matrix visualization** using Matplotlib

# How It Works

The pipeline follows a **strategy consulting style workflow**:

### 1. Company Input

The user provides a company name.

Example:

```
Enter company name: Apple
```

### 2️. AI Product Analysis

The system queries an LLM via the **OpenRouter API** and asks it to:

1. Identify major **products/business units**
2. Define the **target market**
3. Estimate:

   * Market Growth (High / Low)
   * Relative Market Share (High / Low)
4. Assign a **BCG quadrant**
5. Provide **confidence score**

The response is structured as **strict JSON**.

### 3️. Data Processing

The JSON output is parsed and converted into structured data containing:

* Product
* Market
* Market Growth
* Market Share
* BCG Position
* Confidence Score

### 4. Visualization

Products are plotted in a **BCG matrix visualization**:

| Quadrant        | Meaning                        |
| --------------- | ------------------------------ |
| Star          | High growth, high market share |
| Cash Cow     | Low growth, high market share  |
| Question Mark | High growth, low market share  |
| Dog          | Low growth, low market share   |


# Tech Stack

* Python
* OpenRouter API
* GPT-4o-mini (LLM)
* Matplotlib
* NumPy
* Requests

---

# Installation

### 1️. Clone the Repository

```bash
git clone https://github.com/yourusername/bcg-matrix-ai.git
cd bcg-matrix-ai
```

### 2️. Install Dependencies

```bash
pip install matplotlib numpy requests
```

### 3️. Add OpenRouter API Key

Open **bcggrok.py**

Replace:

```python
OPENROUTER_API_KEY = ""
```

with

```python
OPENROUTER_API_KEY = "your_api_key_here"
```

### 4. Running the Project

Run the script:

```bash
python bcggrok.py
```

Then enter a company name:

```
Enter company name: Tesla
```

# Use Cases

This tool can be used for:

• Strategy consulting simulations
• MBA / business school projects
• Competitive product portfolio analysis
• Startup product positioning
• Market research experiments

---
