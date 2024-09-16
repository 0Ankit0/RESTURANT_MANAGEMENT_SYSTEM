namespace RMS_API.Models
{
    public class ResponseModel
    {
        public int status { get; set; }
        public string? Role { get; set; }
        public string? message { get; set; }
        public object data { get; set; }
        public string? TokenNo { get; set; }

    }
}
