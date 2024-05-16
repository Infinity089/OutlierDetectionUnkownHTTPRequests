import pandas as pd
import os
import ipaddress
from user_agents import parse


PATH_HEADER_REDUCTION = 'Header_Reduction/'

# Reads and returns data from a JSON file located at the specified path
def get_data(PATH):
    return pd.read_json(PATH)

# Reads data from a JSON file, splits it into features, and returns the result
def get_data_split(PATH):
    df = get_data(PATH)
    return __split_features(df)

# Reads data, preprocesses it by splitting, removing, padding, and combining features
def get_data_preprocessed(PATH):
    df = get_data(PATH)
    df_origin = df
    df = __split_features(df)
    df = __remove_features(df)
    df = __fill_nan(df)
    df = __pad_data(df)
    df = __combine_features(df)
    return df, df_origin

def get_data_split_header(PATH):
    df = get_data(PATH)
    df_origin = df
    df = __split_header(df)
    df_origin = __split_header(df_origin)
    df_origin = __fill_nan(df_origin)
    df = __fill_nan(df)
    df = __remove_features(df)
    #df = __pad_data(df)
    return df, df_origin

def get_data_reduced_header(PATH):
    df = get_data(PATH)
    df_origin = df
    df = __reduce_Header(df)
    df_origin = __reduce_Header(df_origin)
    df_origin = __fill_nan(df_origin)
    df = __fill_nan(df)
    #df = __split_path(df)
    #df = __split_path_params(df)
    df = __remove_features(df)
    df = __pad_data(df)
    df = __combine_features(df)
    return df, df_origin

def get_data_split_header_ipremove_UAremove(PATH):
    df = get_data(PATH)
    df = __split_header(df)
    features_list = ["Host", "Referer", "X-Forwarded-For", "Origin"]
    for feature in features_list:
        df[feature] = df[feature].apply(__remove_ip)
    df = __remove_UserAgent_feature(df)
    df = __fill_nan(df)
    df_origin = df
    df = __remove_features(df)
    return df, df_origin

# Splits and processes specific columns in the dataframe to create new feature columns
    # (Headers, Path, PathParams)
    # Returns the modified dataframe
    # Contains multiple steps to split and encode categorical data
    # Note: Uses helper function __split_and_remove_nan
    # and other private helper functions (__split_and_remove_nan, __pad_feature, __process_feature)
def __split_features(df):
    df = __split_header(df)
    df = __split_path(df)
    df = __split_path_params(df)
    return df

def __split_header(df):
    headers = df['Headers'].apply(pd.Series)
    #headers = headers.add_prefix('hd_')
    df = pd.concat([df.drop('Headers', axis=1), headers], axis=1)
    return df

def __split_path(df):
    split_paths = df['Path'].str.split('/')
    split_paths = split_paths.apply(lambda x: list(dict.fromkeys(x)))
    unique_paths = pd.DataFrame(split_paths.tolist(), index=split_paths.index)
    dummies = pd.get_dummies(unique_paths.apply(lambda x: pd.Series(x)).stack(),dtype=float).groupby(level=0).max()
    df = df.drop(columns=['Path'])
    df = pd.concat([df, dummies], axis=1)
    return df

def __split_path_params(df):
    split_paths = df['PathParams'].apply(__split_and_remove_nan)
    unique_paths = pd.DataFrame(split_paths.tolist(), index=split_paths.index)
    dummies = pd.get_dummies(unique_paths.apply(lambda x: pd.Series(x)).stack(),dtype=float).groupby(level=0).max()
    df = df.drop(columns=['PathParams'])
    df = pd.concat([df, dummies], axis=1)
    return df

# Splits a string by '&' and removes duplicate values
    # Used in the process of splitting PathParams
def __split_and_remove_nan(x):
    if isinstance(x, str):
        return list(dict.fromkeys(x.split('&')))
    else:
        return []

def __fill_nan (df):
    for column in df.columns:
        df[column].fillna("", inplace=True)
        df[column].replace("NaN","",inplace=True)
        df[column].replace("nan","",inplace=True)

    return df

# Removes specific columns from the dataframe
    # ('Timestamp', 'SourceIP', 'SourcePort')
    # Returns a modified copy of the dataframe    
def __remove_features(df):
    selected_features = [col for col in df.columns if col not in ['Timestamp', 'SourceIP', 'SourcePort']]
    return df[selected_features].copy()

# Applies feature processing and padding to ensure uniform length of features
def __pad_data(data):
    return data.applymap(__process_feature).apply(__pad_feature)

# Pads individual features to a uniform length
def __pad_feature(feature):
    max_length = max(len(val) for val in feature)
    return feature.apply(lambda x: x.ljust(max_length))

# Processes different types of features (strings, dictionaries, etc.) to a uniform format
def __process_feature(feature):
    return str(feature)
    
# Combines all features into a single string representation
def __combine_features(data):
    return data.apply(lambda x: ' '.join(x), axis=1)

def __checkValidIP(ip):
    if ip.startswith("http://") or ip.startswith("https://"):
        ip = ip.split("//")[1].split(":")[0]
    else:
        ip = ip.split(":")[0]
    ip = ip.split("/")[0]
    if "localhost" in ip:
        return True
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def __remove_ip(x):
    x = str(x)
    if __checkValidIP(x):
        return ""
    else:
        return x

def __remove_ip_features(df):
    features_list = ["Host", "Referer", "X-Forwarded-For", "Origin"]
    headers = df["Headers"].apply(pd.Series)#.apply(lambda x: json.loads(x) if isinstance(x, str) else x)
    for feature in features_list:
        headers[feature] = headers[feature].apply(__remove_ip)
    df = df.drop(columns="Headers")
    df = pd.concat([df,headers],axis=1)
    return df

def __check_UserAgents(x):
    x = str(x)
    ua_parse = parse(x)
    if "Other" in ua_parse.browser.family and "Other" in ua_parse.device.family: #First check browser, afterwards os
        return x
    else:
        return "" 
    
def __remove_UserAgent_feature(df):
    df["User-Agent"] = df["User-Agent"].apply(__check_UserAgents)
    return df
    
    

def __reduce_Header(df):
    df = __remove_ip_features(df)
    for filename in os.listdir(PATH_HEADER_REDUCTION):
        if filename.startswith('Header_') and filename.endswith('.txt'):  # Überprüfe, ob der Dateiname mit 'Header_' beginnt und auf '.txt' endet
            file_path = os.path.join(PATH_HEADER_REDUCTION, filename)  # Erstelle den vollständigen Dateipfad
            with open(file_path, 'r') as file:
                lines = [line.rsplit(':', 1)[0] for line in file.readlines()]
            column_name = file_path.split('/')[-1].split('.')[0].split('_')[-1]
            if column_name in df.columns:
                df[column_name] = df[column_name].apply(lambda x: "" if x in lines else x)
    return df
