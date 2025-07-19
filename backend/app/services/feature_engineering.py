import pandas as pd

def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    # Preserve all original columns for behavior profile
    df = df.copy()
    
    # Identify numeric columns and fill NaNs with column means
    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].mean(numeric_only=True))
    
    return df
