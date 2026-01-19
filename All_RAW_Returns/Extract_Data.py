import pandas as pd
import re
import os

def extract_headline(text):
    """Extract text after 'Headline' label (with or without quotes)"""
    if pd.isna(text) or not isinstance(text, str):
        return ""
    # Try with double quotes first
    match = re.search(r'Headline[:\s]*"([^"]*)"', text)
    if match:
        return match.group(1)
    # Try with single quotes
    match = re.search(r"Headline[:\s]*'([^']*)'", text)
    if match:
        return match.group(1)
    # If no quotes, extract text until the next label or newline
    match = re.search(r'Headline[:\s]*(.+?)(?:\n|Tags:|$)', text, re.IGNORECASE)
    return match.group(1).strip() if match else ""

def extract_novice_score(text):
    """Extract decimal value after NOVICE"""
    if pd.isna(text) or not isinstance(text, str):
        return None
    match = re.search(r'NOVICE[:\s]*(-?[\d.]+)', text)
    return float(match.group(1)) if match else None

def extract_fanatic_score(text):
    """Extract decimal value after FANATIC"""
    if pd.isna(text) or not isinstance(text, str):
        return None
    match = re.search(r'FANATIC[:\s]*(-?[\d.]+)', text)
    return float(match.group(1)) if match else None

def extract_dayswing_score(text):
    """Extract decimal value after DAY/SWING"""
    if pd.isna(text) or not isinstance(text, str):
        return None
    match = re.search(r'DAY/SWING[:\s]*(-?[\d.]+)', text)
    return float(match.group(1)) if match else None

def extract_longterm_score(text):
    """Extract decimal value after LONG-TERM"""
    if pd.isna(text) or not isinstance(text, str):
        return None
    match = re.search(r'LONG-TERM[:\s]*(-?[\d.]+)', text)
    return float(match.group(1)) if match else None

def extract_regime(text):
    """Extract REGIME value"""
    if pd.isna(text) or not isinstance(text, str):
        return ""
    match = re.search(r'REGIME[:\s]*([A-Z]+)', text)
    return match.group(1) if match else ""

def extract_line2(text):
    """Extract text after 'Line 2:'"""
    if pd.isna(text) or not isinstance(text, str):
        return ""
    match = re.search(r'Line 2[:\s]*(.+?)(?:\n|$)', text)
    return match.group(1).strip() if match else ""

def calculate_sentiment_score(row):
    """Calculate final sentiment score based on REGIME"""
    # Check if any required values are missing
    if pd.isna(row['NOVICE']) or pd.isna(row['FANATIC']) or pd.isna(row['DAY/SWING']) or pd.isna(row['LONG-TERM']):
        return None
    
    regime = str(row['REGIME']).upper() if pd.notna(row['REGIME']) else ""
    
    if regime == 'MEME':
        # MEME formula: (0.40 × NOVICE) + (0.20 × FANATIC) + (0.30 × DAY/SWING) + (0.10 × LONG-TERM)
        score = (0.40 * row['NOVICE']) + (0.20 * row['FANATIC']) + (0.30 * row['DAY/SWING']) + (0.10 * row['LONG-TERM'])
    else:  # NORMAL or any other value
        # NORMAL formula: (0.20 × NOVICE) + (0.10 × FANATIC) + (0.30 × DAY/SWING) + (0.40 × LONG-TERM)
        score = (0.20 * row['NOVICE']) + (0.10 * row['FANATIC']) + (0.30 * row['DAY/SWING']) + (0.40 * row['LONG-TERM'])
    
    return score

def get_unique_filename(directory, base_name, extension):
    """Generate unique filename if file already exists"""
    filename = f"{base_name}{extension}"
    filepath = os.path.join(directory, filename)
    
    if not os.path.exists(filepath):
        return filepath
    
    counter = 2
    while True:
        filename = f"{base_name} ({counter}){extension}"
        filepath = os.path.join(directory, filename)
        if not os.path.exists(filepath):
            return filepath
        counter += 1

def main():
    # Define file paths
    input_file = r"c:\Users\swara\OneDrive - TUM\Sem 1\Campus Challenge - Investing with AI\CampusChallenge-Group-15\All_RAW_Returns\sentiments_group 15.csv"
    output_dir = r"c:\Users\swara\OneDrive - TUM\Sem 1\Campus Challenge - Investing with AI\CampusChallenge-Group-15\All_RAW_Returns\Extracted Files"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the CSV file
    print("Reading CSV file...")
    try:
        df = pd.read_csv(input_file, encoding='utf-8', low_memory=False)
    except UnicodeDecodeError:
        print("UTF-8 encoding failed, trying latin1...")
        try:
            df = pd.read_csv(input_file, encoding='latin1', low_memory=False)
        except:
            print("latin1 encoding failed, trying cp1252...")
            df = pd.read_csv(input_file, encoding='cp1252', low_memory=False)
    
    # Extract required columns
    print("Extracting data...")
    extracted_df = pd.DataFrame()
    
    # Copy existing columns
    if 'date_day' in df.columns:
        extracted_df['date_day'] = df['date_day']
    if 'Ticker' in df.columns:
        extracted_df['Ticker'] = df['Ticker']
    if 'title' in df.columns:
        extracted_df['title'] = df['title']
    
    # Extract from sentiment column
    if 'sentiment' in df.columns:
        extracted_df['Headline'] = df['sentiment'].apply(extract_headline)
        extracted_df['NOVICE'] = df['sentiment'].apply(extract_novice_score)
        extracted_df['FANATIC'] = df['sentiment'].apply(extract_fanatic_score)
        extracted_df['DAY/SWING'] = df['sentiment'].apply(extract_dayswing_score)
        extracted_df['LONG-TERM'] = df['sentiment'].apply(extract_longterm_score)
        extracted_df['REGIME'] = df['sentiment'].apply(extract_regime)
        extracted_df['Line2'] = df['sentiment'].apply(extract_line2)
    
    # Calculate final sentiment score
    extracted_df['Sentiment_Score'] = extracted_df.apply(calculate_sentiment_score, axis=1)
    
    # Filter out rows with missing required fields
    print("Filtering out incomplete rows...")
    required_columns = ['date_day', 'Ticker', 'Headline', 'NOVICE', 'FANATIC', 'DAY/SWING', 'LONG-TERM', 'REGIME']
    rows_before = len(extracted_df)
    
    # Keep only rows where all required columns have non-null values
    extracted_df = extracted_df.dropna(subset=required_columns)
    
    # Also filter out empty strings in text fields
    extracted_df = extracted_df[
        (extracted_df['Headline'].str.strip() != '') & 
        (extracted_df['REGIME'].str.strip() != '')
    ]
    
    rows_after = len(extracted_df)
    rows_removed = rows_before - rows_after
    
    # Get unique filename
    output_file = get_unique_filename(output_dir, "Extracted_file", ".csv")
    
    # Save to CSV
    extracted_df.to_csv(output_file, index=False)
    print(f"Data extracted successfully!")
    print(f"Rows removed due to missing data: {rows_removed}")
    print(f"Output saved to: {output_file}")
    print(f"Total rows in final file: {len(extracted_df)}")

if __name__ == "__main__":
    main()
