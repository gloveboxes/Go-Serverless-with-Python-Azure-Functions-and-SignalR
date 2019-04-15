import logging
import azure.functions as func
from azure.cosmosdb.table.tableservice import TableService
import requests
import json
import os
from ..SharedCode import calibrate

# https://azure.microsoft.com/en-au/blog/managing-concurrency-in-microsoft-azure-storage-2/
# https://docs.microsoft.com/en-us/python/api/azure-cosmosdb-table/azure.cosmosdb.table.tableservice.tableservice?view=azure-python

deviceStateTable = "DeviceState"
calibrationTable = "Calibration"

storageConnectionString = os.environ['StorageConnectionString']
partitionKey = os.environ.get('PartitionKey', 'Sydney')
signalrUrl = os.environ['SignalrUrl']

table_service = TableService(connection_string=storageConnectionString)
if not table_service.exists(deviceStateTable):
    table_service.create_table(deviceStateTable)

calibrator = calibrate.Calibrate(table_service, calibrationTable, partitionKey)


def main(event: func.EventHubEvent):

    messages = json.loads(event.get_body().decode('utf-8'))
    signalrUpdates = {}

    # Batch calibrate telemetry
    for telemetry in messages:
        try:
            entity = updateDeviceState(telemetry)
            if entity is not None:
                signalrUpdates[entity.get('DeviceId')] = entity

        except Exception as err:
            logging.info('Exception occurred {0}'.format(err))

    for item in signalrUpdates:
        notifySignalR(signalrUpdates.get(item))


def updateDeviceState(telemetry):
    mergeRetry = 0

    while mergeRetry < 10:
        mergeRetry += 1

        try:
            # get existing telemetry entity
            entity = table_service.get_entity(
                deviceStateTable, partitionKey, telemetry.get('deviceId', telemetry.get('DeviceId')))
            etag = entity.get('etag')
            count = entity.get('Count', 0)
        except:
            entity = {}
            etag = None
            count = 0

        count += 1

        updateEntity(telemetry, entity, count)
        calibrator.calibrateTelemetry(entity)

        if not validateTelemetry(entity):
            break

        try:
            if etag is not None:    # if etag found then record existed
                # try a merge - it will fail if etag doesn't match
                table_service.merge_entity(
                    deviceStateTable, entity, if_match=etag)
            else:
                table_service.insert_entity(deviceStateTable, entity)

            return entity

        except:
            pass

    else:
        logging.info('Failed to commit update for device {0}'.format(
            entity.get('DeviceId')))


def updateEntity(telemetry, entity, count):
    entity['PartitionKey'] = partitionKey
    entity['RowKey'] = telemetry.get('deviceId', telemetry.get('DeviceId'))
    entity['DeviceId'] = entity.get('RowKey')
    entity['Geo'] = telemetry.get('geo', telemetry.get('Geo', 'Sydney'))
    entity['Humidity'] = telemetry.get('humidity', telemetry.get('Humidity'))
    entity['hPa'] = telemetry.get('pressure', telemetry.get(
        'Pressure', telemetry.get('hPa', telemetry.get('HPa'))))
    entity['Celsius'] = telemetry.get('temperature', telemetry.get(
        'Temperature', telemetry.get('Celsius')))
    entity['Light'] = telemetry.get('Light', telemetry.get('light'))
    entity['Id'] = telemetry.get('messageId', telemetry.get('Id'))
    entity['Count'] = count
    entity['Schema'] = 1
    entity['etag'] = None


def notifySignalR(telemetry):
    try:
        signalrMsg = {"DeviceId": telemetry.DeviceId, "Celsius": telemetry.Celsius,
                      "Pressure": telemetry.hPa, "Humidity": telemetry.Humidity, "Count": telemetry.Count}

        headers = {'Content-type': 'application/json'}
        r = requests.post(signalrUrl, data=json.dumps(
            signalrMsg), headers=headers)
    except Exception as ex:
        msg = ex


def validateTelemetry(telemetry):
    temperature = telemetry.get('Celsius')
    pressure = telemetry.get('hPa')
    humidity = telemetry.get('Humidity')

    if temperature is not None and not -40 <= temperature <= 80:
        return False
    if pressure is not None and not 600 <= pressure <= 1600:
        return False
    if humidity is not None and not 0 <= humidity <= 100:
        return False
    return True
