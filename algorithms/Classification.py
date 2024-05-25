import os
import pandas as pd
# import datetime
# import numpy as np
from numpy import *
# import math
# import pickle
# from scipy.stats.stats import pearsonr
# import matplotlib.pyplot as plt
import sys
# import argparse
from Networks_pytorch import *
from Dataset_manipulation import *
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")
from sklearn.ensemble import RandomForestClassifier
# from sklearn.metrics import mean_squared_error, mean_absolute_error, f1_score, recall_score, precision_score
from sklearn.utils import shuffle


def classification(X_train, Y_train, X_test, Y_test, classifier, metric, **args):
    """
    Perform classification using the specified classifier.
    --- Step 1.7: Perform Classification
    Parameters:
    - X_train (array-like): Training data features.
    - Y_train (array-like): Training data labels.
    - X_test (array-like): Test data features.
    - Y_test (array-like): Test data labels.
    - classifier (str): The classifier to use. Options: 'RandomForest', 'TCN', 'LSTM'.
    - metric (str): The metric to evaluate the classification performance.
    - **args: Additional arguments specific to each classifier.

    Returns:
    - None
    """
    print('Classification using {} is starting'.format(classifier))
    Y_test_real = []
    prediction = []
    if classifier == 'RandomForest':
        # Step 1.7.1: Perform Classification using RandomForest: Use RandomForest Libaray. Train and validate the network using RandomForest.
        X_train, Y_train = shuffle(X_train, Y_train)
        # Use third-party RandomForest library.
        model = RandomForestClassifier(n_estimators=30, min_samples_split=10, random_state=3)
        model.fit(X_train[:, :], Y_train)
        prediction = model.predict(X_test)
        Y_test_real = Y_test
        report_metrics(Y_test_real, prediction, metric)
    elif classifier == 'TCN':
        # Step 1.7.2: Perform Classification using TCN. Subflowchart: TCN Subflowchart. Train and validate the network using TCN
        net_train_validate_TCN(args['net'], args['optimizer'], X_train, Y_train, X_test, Y_test, args['epochs'], args['batch_size'], args['lr'])
    elif classifier == 'LSTM':
        # Step 1.7.3: Perform Classification using LSTM. Subflowchart: LSTM Subflowchart. Train and validate the network using LSTM
        train_dataset = FPLSTMDataset(X_train, Y_train)
        train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=args['batch_size'], shuffle=True, collate_fn=FPLSTM_collate)
        test_dataset = FPLSTMDataset(X_test, Y_test.values)
        test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=args['batch_size'], shuffle=True, collate_fn=FPLSTM_collate)
        net_train_validate_LSTM(args['net'], args['optimizer'], train_loader, test_loader, args['epochs'], X_test.shape[0], Xtrain.shape[0], args['lr'])
        pass

if __name__ == '__main__':
    # ------------------ #
    # Feature Selection Subflowchart 
    # Step 1: Define empty lists and dictionary
    features = {
        'Xiao_et_al': [
            'date',
            'serial_number',
            'model',
            'failure',
            'smart_1_normalized', 
            'smart_5_normalized',
            'smart_5_raw',
            'smart_7_normalized',
            'smart_9_raw',
            'smart_12_raw',
            'smart_183_raw',
            'smart_184_normalized',
            'smart_184_raw', 
            'smart_187_normalized',
            'smart_187_raw',
            'smart_189_normalized', 
            'smart_193_normalized',
            'smart_193_raw',
            'smart_197_normalized', 
            'smart_197_raw',
            'smart_198_normalized',
            'smart_198_raw',
            'smart_199_raw'
        ],
        'iSTEP': [
            'date',
            'serial_number',
            'model',
            'failure',
            'smart_5_raw',
            'smart_3_raw', 
            'smart_10_raw',
            'smart_12_raw',
            'smart_4_raw',
            'smart_194_raw', 
            'smart_1_raw',
            'smart_9_raw',
            'smart_192_raw',
            'smart_193_raw', 
            'smart_197_raw',
            'smart_198_raw',
            'smart_199_raw'
        ]
    }
    #model = 'ST4000DM000'
    # here you can select the model. This is the one tested.
    model = 'ST3000DM001'
    #years = ['2016', '2017', '2018']
    
    # Correct years for the model
    years = ['2013', '2014', '2015', '2016', '2017']
    # many parameters that could be changed, both for unbalancing, for networks and for features.
    windowing = True
    min_days_HDD = 115
    # TODO: Can be adjusted by dynamic parameters
    days_considered_as_failure = 7
    test_train_perc = 0.3
    # type of oversampling
    oversample_undersample = 2
    # balancing factor (major/minor = balancing_normal_failed)
    # TODO: We can calculate the imbalance ratio of the dataset and use this ratio to adjust the balancing factor.
    balancing_normal_failed = 20
    history_signal = 32
    # type of classifier
    classifier = 'TCN'
    # if you extract features for RF for example. Not tested
    perform_features_extraction = False
    CUDA_DEV = "0"
    # if automatically select best features
    ranking = 'Ok'
    num_features = 18
    overlap = 1

    script_dir = os.path.dirname(os.path.abspath(__file__))

    try:
        # Step 1: Load the dataset from pkl file.
        df = pd.read_pickle(os.path.join(script_dir, '..', 'output', f'{model}_Dataset_windowed_{history_signal}_rank_{ranking}_{num_features}_overlap_{overlap}.pkl'))
    except:
        # Step 1.1: Import the dataset from the raw data.
        if ranking == 'None':
            df = import_data(years=years, model=model, name='iSTEP', features=features)
        else:
            df = import_data(years=years, model=model, name='iSTEP')
        df.set_index(['serial_number', 'date'], inplace=True)
        print("DF index name:", df.index.names)
        print(df.head())
        for column in list(df):
            missing = round(df[column].notna().sum() / df.shape[0] * 100, 2)
            print('{:.<27}{}%'.format(column, missing))
        # drop bad HDs
        # Step 1.2: Filter out the bad HDDs.
        bad_missing_hds, bad_power_hds, df = filter_HDs_out(df, min_days=min_days_HDD, time_window='30D', tolerance=30)
        # predict_val represents the prediction value of the failure
        # validate_val represents the validation value of the failure
        # Step 1.3: Define RUL(Remain useful life) Piecewise
        df['predict_val'], df['validate_val'] = generate_failure_predictions(df, days=days_considered_as_failure, window=history_signal)
        if ranking != 'None':
            # Step 1.4: Feature Selection: Subflow chart of Main Classification Process
            df = feature_selection(df, num_features)
        print('Used features')
        for column in list(df):
            print('{:.<27}'.format(column,))
        # print('Saving to pickle file...')
        #df.to_pickle(os.path.join(script_dir, '..', 'output', f'{model}_Dataset_windowed_{history_signal}_rank_{ranking}_{num_features}_overlap_{overlap}.pkl'))

    ## -------- ##
    # random: stratified without keeping time order
    # hdd --> separate different hdd (need FIXes)
    # temporal --> separate by time (need FIXes)
    # Step 1.5: Partition the dataset into training and testing sets. Partition Dataset: Subflow chart of Main Classification Process
    Xtrain, Xtest, ytrain, ytest = DatasetPartitioner(
        df,
        model,
        overlap=overlap,
        rank=ranking,
        num_features=num_features,
        technique='random',
        test_train_perc=test_train_perc,
        enable_windowing=windowing,
        window_dim=history_signal,
        resampler_balancing=balancing_normal_failed,
        oversample_undersample=oversample_undersample
    )

    # Step 1.6: Classifier Selection: set training parameters
    ####### CLASSIFIER PARAMETERS #######
    if classifier == 'RandomForest':
        # Step 1.6.1: Set training parameters for RamdomForest. Use RandomForest Libaray
        pass
    elif classifier == 'TCN':
        # Step 1.6.2: Set training parameters for TCN. Subflowchart: TCN Subflowchart.
        os.environ["CUDA_VISIBLE_DEVICES"] = CUDA_DEV
        batch_size = 256
        lr = 0.001
        num_inputs = Xtrain.shape[1]
        net, optimizer = init_net(lr, history_signal, num_inputs)
        epochs = 200
    elif classifier == 'LSTM':
        # Step 1.6.3: Set training parameters for LSTM. Subflowchart: LSTM Subflowchart.
        lr = 0.001
        batch_size = 256
        epochs = 300
        dropout = 0.1
        #hidden state sizes (from [14])
        # The dimensionality of the output space of the LSTM layer
        lstm_hidden_s = 64
        # The dimensionality of the output space of the first fully connected layer
        fc1_hidden_s = 16
        num_inputs = Xtrain.shape[1]
        net = FPLSTM(lstm_hidden_s, fc1_hidden_s, num_inputs, 2, dropout)
        net.cuda()
        # We use the Adam optimizer, a method for Stochastic Optimization
        optimizer = optim.Adam(net.parameters(), lr=lr)
    ## ---------------------------- ##

    # Step x.1: Feature Extraction
    if perform_features_extraction == True: 
        # Extract features for the train and test set
        Xtrain = feature_extraction(Xtrain)
        Xtest = feature_extraction(Xtest)
    # Step x.2: Reshape the data for RandomForest: We jumped from Step 1.6.1, use third-party RandomForest library
    if classifier == 'RandomForest' and windowing == 1:
        Xtrain = Xtrain.reshape(Xtrain.shape[0], Xtrain.shape[1] * Xtrain.shape[2])
        Xtest = Xtest.reshape(Xtest.shape[0], Xtest.shape[1] * Xtest.shape[2])

    try:
        classification(
            X_train=Xtrain,
            Y_train=ytrain,
            X_test=Xtest,
            Y_test=ytest,
            classifier=classifier,
            metric=['RMSE', 'MAE', 'FDR', 'FAR', 'F1', 'recall', 'precision'],
            net=net,
            optimizer=optimizer,
            epochs=epochs,
            batch_size=batch_size,
            lr=lr
        )
    except:
        classification(
            X_train=Xtrain,
            Y_train=ytrain,
            X_test=Xtest,
            Y_test=ytest,
            classifier=classifier,
            metric=['RMSE', 'MAE', 'FDR', 'FAR', 'F1', 'recall', 'precision']
        )