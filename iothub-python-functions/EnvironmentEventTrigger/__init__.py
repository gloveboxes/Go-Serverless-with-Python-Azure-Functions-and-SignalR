import logging
import azure.functions as func
from azure.cosmosdb.table.tableservice import TableService
import requests
import json
import os

# https://azure.microsoft.com/en-au/blog/managing-concurrency-in-microsoft-azure-storage-2/
# https://docs.microsoft.com/en-us/python/api/azure-cosmosdb-table/azure.cosmosdb.table.tableservice.tableservice?view=azure-python

environmentTable = "Environment"
calibrationTable = "Calibration"

storageConnectionString = os.environ['StorageConnectionString']
partitionKey = os.environ['PartitionKey']
signalrUrl = os.environ['SignalrUrl']

calibrationDictionary = {}

table_service = TableService(connection_string=storageConnectionString)
if not table_service.exists(environmentTable):
    table_service.create_table(environmentTable)
if not table_service.exists(calibrationTable):
    table_service.create_table(calibrationTable)


def main(event: func.EventHubEvent):

    messages = json.loads(event.get_body().decode('utf-8'))
    stateUpdates = []

    # Batch calibrate telemetry
    for telemetry in messages:
        calibrateTelemetry(telemetry)
        stateUpdates.append(telemetry)

    # Batch update telemetry state
    for telemetry in stateUpdates:
        updateEnvironment(telemetry)
        # notifyClients(signalrUrl, telemetry)


def updateEnvironment(telemetry):
    success = False
    mergeRetry = 0

    while not success and mergeRetry < 10:
        mergeRetry = mergeRetry + 1
        count = 0
        entity = {}

        try:
            # get existing telemetry entity
            entity = table_service.get_entity(
                environmentTable, partitionKey, telemetry['DeviceId'])
            if 'Count' in entity:
                count = entity['Count']
        except:
            count = 0

        count = count + 1
        updateEntity(telemetry, entity, count)
        
        if 'etag' in entity:    # if etag found then record existed
            try:
                # try a merge - it will fail if etag doesn't match
                etag = table_service.merge_entity(
                    environmentTable, entity, if_match=entity['etag'])
                success = True
            except:
                success = False
        else:
            try:
                table_service.insert_entity(environmentTable, entity)
                success = True
            except:
                success = False


def updateEntity(telemetry, entity, count):
    entity['PartitionKey'] = partitionKey
    entity['RowKey'] = telemetry['DeviceId']
    entity['DeviceId'] = telemetry['DeviceId']
    entity['Geo'] = telemetry['Geo']
    entity['Humidity'] = telemetry['Humidity']
    entity['HPa'] = telemetry['HPa']
    entity['Celsius'] = telemetry['Celsius']
    entity['Light'] = telemetry['Light']
    entity['Id'] = telemetry['Id']
    entity['Count'] = count


def notifyClients(signalrUrl, telemetry):
    headers = {'Content-type': 'application/json'}
    r = requests.post(signalrUrl, data=json.dumps(
        telemetry), headers=headers)
    logging.info(r)


def calibrateTelemetry(telemetry):
    calibrationData = getCalibrationData(telemetry['DeviceId'])

    if calibrationData is not None:
        telemetry["Celsius"] = calibrate(
            telemetry["Celsius"], calibrationData["TemperatureSlope"], calibrationData["TemperatureYIntercept"])
        telemetry["Humidity"] = calibrate(
            telemetry["Humidity"], calibrationData["HumiditySlope"], calibrationData["HumidityYIntercept"])
        telemetry["HPa"] = calibrate(
            telemetry["HPa"], calibrationData["PressureSlope"], calibrationData["PressureYIntercept"])


def calibrate(value, slope, intercept):
    return value * slope + intercept


def getCalibrationData(deviceId):
    if deviceId not in calibrationDictionary:
        try:
            calibrationDictionary[deviceId] = table_service.get_entity(
                calibrationTable, partitionKey, deviceId)
        except:
            calibrationDictionary[deviceId] = None

    return calibrationDictionary[deviceId]
