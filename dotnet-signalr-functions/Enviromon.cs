using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.Azure.WebJobs.Extensions.SignalRService;
using Microsoft.Extensions.Logging;
using Microsoft.WindowsAzure.Storage.Table;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;


namespace Glovebox.Functions
{
    public static class Enviromon
    {

        [FunctionName("SendSignalrMessage")]
        public static Task Run(
            [HttpTrigger(AuthorizationLevel.Function, "post", Route = null)] HttpRequest req,
            [SignalR(HubName = "Enviromon")] IAsyncCollector<SignalRMessage> signalRMessages,
            ILogger log)
        {

            string requestBody = new StreamReader(req.Body).ReadToEnd();

            return signalRMessages.AddAsync(
                new SignalRMessage
                {
                    Target = "newMessage",
                    Arguments = new[] { requestBody }
                });
        }


        [FunctionName("negotiate")]
        public static SignalRConnectionInfo Negotiate(
            [HttpTrigger(AuthorizationLevel.Anonymous)]HttpRequest req,
            [SignalRConnectionInfo(HubName = "Enviromon")]SignalRConnectionInfo connectionInfo)
        {
            return connectionInfo;
        }


        [FunctionName("getdevicestate")]
        public static Task DeviceState(
            [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = null)] HttpRequest req,
            [SignalR(HubName = "Enviromon")] IAsyncCollector<SignalRMessage> signalRMessages,
            [Table("DeviceState", Connection = "StorageConnectionString")]  CloudTable deviceStateTable,
            ILogger log)
        {

            var querySegment = deviceStateTable.ExecuteQuerySegmentedAsync(new TableQuery<EnvironmentEntity>(), null);
            var result = querySegment.Result.ToList();
            string json = JsonConvert.SerializeObject(result);

            return signalRMessages.AddAsync(
                new SignalRMessage
                {
                    Target = "newMessage",
                    Arguments = new[] { json }
                });
        }
    }

    public class EnvironmentEntity : TableEntity
    {
        public string DeviceId { get; set; }
        public double Celsius { get; set; }
        public long Count { get; set; }
    }
}