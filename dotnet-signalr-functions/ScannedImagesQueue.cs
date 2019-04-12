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
    public static class ScannedImagesQueue
    {

        [FunctionName("SendSignalrMessage")]
        public static Task Run(
            [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = null)] HttpRequest req,
            [SignalR(HubName = "Classified")] IAsyncCollector<SignalRMessage> signalRMessages,
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
            [SignalRConnectionInfo(HubName = "Classified")]SignalRConnectionInfo connectionInfo)
        {
            return connectionInfo;
        }
        

        [FunctionName("getimagestate")]
        public static Task ImageState(
            [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = null)] HttpRequest req,
            [SignalR(HubName = "Classified")] IAsyncCollector<SignalRMessage> signalRMessages,
            [Table("Classified", Connection = "StorageConnectionString")]  CloudTable testTable,
            ILogger log)
        {

            var querySegment = testTable.ExecuteQuerySegmentedAsync(new TableQuery<ClassifiedEntity>(), null);
            var result = querySegment.Result.ToList();
            string json = JsonConvert.SerializeObject(result);

            // string requestBody = new StreamReader(req.Body).ReadToEnd();

            return signalRMessages.AddAsync(
                new SignalRMessage
                {
                    Target = "newMessage",
                    Arguments = new[] { json }
                });
        }
    }

    public class ClassifiedEntity : TableEntity
    {
        public long Count { get; set; }
        public string Tag { get; set; }
        public double Probability { get; set; }
    }
}