""" Sample prediction submission pipeline in python 3 """
import os
import numerapi
import numpy as np
import pandas as pd
import logging
import joblib
import dotenv
dotenv.load_dotenv() # loads API secrets from .env file
model_name='AZURE_DEPLOY_TEST'

# initialize Numerai API client
napi = numerapi.NumerAPI(public_id=os.environ["NUMERAI_PUBLIC_ID"],secret_key=os.environ["NUMERAI_SECRET_KEY"])

def neutralize(predictions, features, proportion=1.0):
    """
    Feature neutralization to reduce feature exposure (over-reliance on a single feature)
    See: https://forum.numer.ai/t/an-introduction-to-feature-neutralization-exposure/4955
    """
    # given predictions p and feature matrix F, the orthogonal component p' with regards to F is:
    # p' = p - (F dot (F_inverse dot p))
    inverse_features = np.linalg.pinv(features.values, rcond=1e-6)
    exposure = proportion * features.values.dot(inverse_features.dot(predictions))
    return predictions - exposure


def main():
    """ Download, predict and submit for this model """
    
    # Download latest live round parquet file with Numerapi
    current_round = napi.get_current_round()
    v4_1_live_data_location=f"data/v4.1/live/round_{current_round}.parquet"
    napi.download_dataset("v4.1/live_int8.parquet",
                          v4_1_live_data_location)

    # Load the live V4.1 data
    v4_1_live_df=pd.read_parquet(v4_1_live_data_location)
    # Fill missing values with median
    all_features=[feat for feat in v4_1_live_df.columns if feat.startswith('feature_')]
    v4_1_live_df[all_features]=v4_1_live_df[all_features].fillna(v4_1_live_df[all_features].median(skipna=True)).astype("int8")
    
    # Load the trained model
    trained_example_model=joblib.load('models/example_lgbm_target_cyrus.pkl')

    # Make prediction (non-neutralized)
    v4_1_live_df['original_prediction']=trained_example_model.predict(v4_1_live_df[trained_example_model.feature_name_])
    
    # Generate neutralized prediction
    v4_1_live_df['prediction']=neutralize(v4_1_live_df['original_prediction'],
                                          v4_1_live_df[all_features],
                                          proportion=0.25)

    # Save the model prediction
    saved_location=f"submissions/example_prediction_round{current_round}.csv"
    
    # Submission format: id | prediction
    submission_df=v4_1_live_df['prediction'].copy().reset_index()
    submission_df.to_csv(saved_location,index = False)
        
    # Get the list of model ids
    model_ids=napi.get_models()
    curr_model_id = model_ids.get(model_name.lower(),'') # keys of the model_ids dict are all lowercased
    
    # Submit via Numerapi
    submission_id = napi.upload_predictions(saved_location, model_id=curr_model_id)
    logging.info(f'Model: {model_name} submission completed!')

if __name__ == '__main__':
    main()
