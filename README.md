# Create Python Virtual Environment

## Creating your first Python Azure Function

To understand how to create your first Python Azure function then read the "[Create your first Python function in Azure ](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-first-function-python)" article.

## Solution overview

![solution overview](./docs/resources/python-azure-functions-solution.png)

In Bash

```bash
python3.6 -m venv .env
source .env/bin/activate
```

In PowerShell
```powershell
py -3.6 -m venv .env
.env\scripts\activate
```

## Opening Python Project

Be sure that the virtual Python environment you created is active and select in Visual Studio Code

## Deploy Function

func azure functionapp publish enviromon-python --build-native-deps

## Solution components

1. [Image Classifier running on Azure IoT Edge].(https://github.com/gloveboxes/Creating-an-image-recognition-solution-with-Azure-IoT-Edge-and-Azure-Cognitive-Services). This project is configured for Raspberry Pi 2, 3 (A+ or B+) or Linux Desktop as Docker camera pass-through is required.

2. Azure IoT Hub Python Functions (included in this GitHub repo). This project is responsible for reacting to new telemetry from Azure IoT Hub, updating the Classified Storage Table and passing telemetry to the Azure SignalR service for near real-time web client update.

3. Azure SignalR .NET Core Function (Included in this GitHub repo). This Azure Function is responsible for distribution of new telemetry messaged out to the Web Client (https://enviro.z8.web.core.windows.net/image.html)

4. [Web Dashboard](https://enviro.z8.web.core.windows.net/classified.html) (Included in this GitHub repo). This is a Single Page Web App that is hosted on Azure Storage as a Static Website. So it too is serverless. The page used for this sample is classified.html. Be sure to modify the "apiBaseUrl" url to point your instance of the Azure SignalR Azure Function you install.