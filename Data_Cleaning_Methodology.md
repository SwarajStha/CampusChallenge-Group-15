# Data Cleaning and Extraction Methodology

## Overview
This section details the comprehensive data cleaning and extraction process applied to the raw sentiment analysis data contained in `sentiments_group 15.csv`. The process involves parsing unstructured text data, extracting structured information, calculating sentiment scores, and implementing multiple validation and filtering steps to ensure data quality and integrity.

#### Summary of clean-up
- **Rows removed due to missing data**: 92.
- **Rows removed due to Ticker mismatches**: 1272 (2.14% of initial rows).
- **Total rows in final file**: 58136.

## 1. Data Extraction Process

### 1.1 Source Data Structure
The input file (`sentiments_group 15.csv`) contains sentiment analysis results stored in an unstructured text format within a `sentiment` column. Each entry includes multiple components embedded as text, including headlines, investor perspective scores, market regime classifications, and computed sentiment metrics.

### 1.2 Regex-Based Extraction Functions
A series of specialized extraction functions were developed using regular expressions to parse and extract specific data elements from the unstructured sentiment text:

**Text Extraction:**
- **Headline Extraction**: Identifies and extracts news headlines from the sentiment text, handling multiple quote styles (double quotes, single quotes, or no quotes) to ensure robust extraction across different formatting patterns.
- **Line 2 Extraction**: Extracts supplementary analysis text following the "Line 2:" label.
- **Ticker Extraction**: Extracts the stock ticker symbol embedded within the sentiment text for validation purposes.

**Numerical Score Extraction:**
- **NOVICE Score**: Captures the sentiment score assigned to novice investor perspective (-1.0 to +1.0 scale).
- **FANATIC Score**: Extracts the sentiment score for fanatic investor perspective.
- **DAY/SWING Score**: Retrieves the sentiment score for day/swing trading perspective.
- **LONG-TERM Score**: Obtains the sentiment score for long-term investor perspective.
- **FINAL_WEIGHTED Score**: Extracts the pre-calculated weighted sentiment score for validation purposes.

**Categorical Extraction:**
- **REGIME Classification**: Identifies the market regime classification (NORMAL or MEME) which determines the weighting formula for sentiment calculation.

## 2. Sentiment Score Calculation

### 2.1 Weighting Methodology
The final sentiment score is calculated using a regime-specific weighted average of the four investor perspective scores:

**NORMAL Regime Formula:**
$$\text{Sentiment Score} = (0.20 \times \text{NOVICE}) + (0.10 \times \text{FANATIC}) + (0.30 \times \text{DAY/SWING}) + (0.40 \times \text{LONG-TERM})$$

**MEME Regime Formula:**
$$\text{Sentiment Score} = (0.40 \times \text{NOVICE}) + (0.20 \times \text{FANATIC}) + (0.30 \times \text{DAY/SWING}) + (0.10 \times \text{LONG-TERM})$$

The NORMAL regime places greater emphasis on long-term investor perspectives, while the MEME regime prioritizes novice investor sentiment, reflecting different market dynamics.

### 2.2 Precision Standardization
All sentiment scores are standardized to six decimal places (x.xxxxxx format) to ensure uniformity and facilitate precise numerical comparisons during validation and analysis.

## 3. Data Quality Validation and Filtering

The data cleaning process implements a multi-stage filtering approach to ensure data integrity:

### 3.1 Stage 1: Missing Data Filtering
Records with missing or null values in any of the following required fields are removed:
- `date_day` (temporal identifier)
- `Ticker` (stock symbol)
- `Headline` (news headline text)
- `NOVICE`, `FANATIC`, `DAY/SWING`, `LONG-TERM` (investor perspective scores)
- `REGIME` (market classification)

Additionally, records with empty string values in text fields (`Headline` and `REGIME`) are filtered out to prevent downstream processing errors.

### 3.2 Stage 2: Ticker Validation Filtering
A critical validation step compares the original `Ticker` column with the extracted `Ticker(in_sentiment)` from the sentiment text. This cross-validation ensures that the sentiment analysis was performed on the correct stock:

- **Validation Logic**: Records where `Ticker ≠ Ticker(in_sentiment)` are flagged as ticker mismatches.
- **Action**: All mismatched records are removed from the final dataset.
- **Rationale**: Ticker mismatches indicate potential data corruption, incorrect sentiment assignments, or processing errors that could compromise analysis accuracy.

## 4. Quality Assurance Verification

### 4.1 Interactive Data Analysis (`data_analysis.ipynb`)
A Jupyter notebook was developed to perform post-extraction quality checks:

**Ticker Consistency Analysis:**
```python
ticker_mismatches = extracted_data[extracted_data['Ticker'] != extracted_data['Ticker(in_sentiment)']]
```
This comparison identifies any remaining ticker discrepancies and reports the specific rows affected.

**Sentiment Score Validation:**
```python
score_mismatches = extracted_data[
    (extracted_data['Sentiment_Score'] - extracted_data['Final_Weighted']).abs() > 0.000001
]
```
This validation compares our independently calculated `Sentiment_Score` against the `Final_Weighted` score extracted from the sentiment text, using a tolerance threshold of 0.000001 to account for floating-point precision. Any discrepancies beyond this threshold are flagged for review.

## 5. Output and Reporting

### 5.1 Output File Structure
The cleaned data is exported to a structured CSV file with the following columns:
- `date_day`: Date of the news event
- `Ticker`: Stock ticker symbol
- `title`: Original article title
- `Headline`: Extracted headline from sentiment analysis
- `Ticker(in_sentiment)`: Ticker extracted from sentiment text (for validation)
- `NOVICE`, `FANATIC`, `DAY/SWING`, `LONG-TERM`: Individual investor perspective scores
- `REGIME`: Market regime classification
- `Line2`: Supplementary analysis text
- `Sentiment_Score`: Calculated weighted sentiment score (6 decimal places)
- `Final_Weighted`: Extracted reference score (6 decimal places)

### 5.2 Process Metrics
The extraction script provides comprehensive reporting metrics:
- Total number of rows removed due to missing data
- Number of rows removed due to ticker mismatches
- Percentage of initial rows removed for ticker validation failures
- Final row count in the cleaned dataset

## 6. Data Integrity Results

The cleaning process successfully identified approximately 1,272 records with ticker mismatches, representing a significant data quality issue in the original dataset. These records were systematically removed to ensure the final dataset contains only validated, high-quality sentiment analysis results suitable for downstream financial analysis and modeling applications.

This rigorous multi-stage cleaning methodology ensures that the final dataset maintains high standards of accuracy, consistency, and reliability for subsequent investment analysis and decision-making processes.
