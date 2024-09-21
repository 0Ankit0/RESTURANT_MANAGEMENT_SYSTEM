using Microsoft.AspNetCore.Http;
using Newtonsoft.Json;
using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Claims;
using System.Text;
using System.Threading.Tasks;

namespace RMS_FRONTEND.Classes
{
    public interface IApiCall
    {
        Task<string> GetAsync(string endpoint, string id = "");
        Task<string> PostAsync(string endpoint, string content = "");
        Task<string> PostAsync(string endpoint, object data = null);
        Task<string> PostFileAsync(string endpoint, IFormFile file);
        Task<string> PutAsync(string endpoint, string content = "");
        Task<string> PutAsync(string endpoint, object data = null);
        Task<string> PatchAsync(string endpoint, string content = "");
        Task<string> PatchAsync(string endpoint, object data = null);
        Task<string> DeleteAsync(string endpoint, string id = "");
    }

    public class Apicall : IApiCall
    {
        private readonly HttpClient _httpClient;
        private readonly string _baseAddress;

        public Apicall(IConfiguration configuration, IHttpContextAccessor httpContextAccessor)
        {
            _baseAddress = configuration.GetConnectionString("ApiBaseUrl");
            _httpClient = new HttpClient { BaseAddress = new Uri(_baseAddress) };

            var token = httpContextAccessor.HttpContext?.User?.FindFirst(ClaimTypes.Authentication)?.Value;

            if (!string.IsNullOrEmpty(token))
            {
                _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
            }
        }

        // GET: Parameterized and Parameterless
        public async Task<string> GetAsync(string endpoint, string id = "")
        {
            try
            {
                var fullEndpoint = string.IsNullOrWhiteSpace(id) ? endpoint :Path.Combine(endpoint,id);
                HttpResponseMessage response = await _httpClient.GetAsync(fullEndpoint);
                //response.EnsureSuccessStatusCode();
                return await response.Content.ReadAsStringAsync();
            }
            catch (Exception ex)
            {
                string Exception = ex.ToString();
                var ExceptionSubstring = Exception.Substring(0, 1500);
                throw new Exception(ExceptionSubstring);
            }
        }

        // POST: Parameterized (string content or object data)
        public async Task<string> PostAsync(string endpoint, string content = "")
        {
            return await PostAsyncInternal(endpoint, content);
        }

        public async Task<string> PostAsync(string endpoint, object data = null)
        {
            string jsonContent = data != null ? JsonConvert.SerializeObject(data) : "";
            return await PostAsyncInternal(endpoint, jsonContent);
        }

        private async Task<string> PostAsyncInternal(string endpoint, string content)
        {
            try
            {
                HttpContent httpContent = new StringContent(content, Encoding.UTF8, "application/json");
                HttpResponseMessage response = await _httpClient.PostAsync(endpoint, httpContent);
                //response.EnsureSuccessStatusCode();
                return await response.Content.ReadAsStringAsync();
            }
            catch (Exception ex)
            {
                string Exception = ex.ToString();
                var ExceptionSubstring = Exception.Substring(0, 1500);
                throw new Exception(ExceptionSubstring);
            }
        }

        // PUT: Parameterized (string content or object data)
        public async Task<string> PutAsync(string endpoint, string content = "")
        {
            return await PutAsyncInternal(endpoint, content);
        }

        public async Task<string> PutAsync(string endpoint, object data = null)
        {
            string jsonContent = data != null ? JsonConvert.SerializeObject(data) : "";
            return await PutAsyncInternal(endpoint, jsonContent);
        }

        private async Task<string> PutAsyncInternal(string endpoint, string content)
        {
            try
            {
                HttpContent httpContent = new StringContent(content, Encoding.UTF8, "application/json");
                HttpResponseMessage response = await _httpClient.PutAsync(endpoint, httpContent);
                //response.EnsureSuccessStatusCode();
                return await response.Content.ReadAsStringAsync();
            }
            catch (Exception ex)
            {
                string Exception = ex.ToString();
                var ExceptionSubstring = Exception.Substring(0, 1500);
                throw new Exception(ExceptionSubstring);
            }
        }

        // PATCH: Parameterized (string content or object data)
        public async Task<string> PatchAsync(string endpoint, string content = "")
        {
            return await PatchAsyncInternal(endpoint, content);
        }

        public async Task<string> PatchAsync(string endpoint, object data = null)
        {
            string jsonContent = data != null ? JsonConvert.SerializeObject(data) : "";
            return await PatchAsyncInternal(endpoint, jsonContent);
        }

        private async Task<string> PatchAsyncInternal(string endpoint, string content)
        {
            try
            {
                HttpContent httpContent = new StringContent(content, Encoding.UTF8, "application/json");
                HttpRequestMessage request = new HttpRequestMessage(new HttpMethod("PATCH"), endpoint)
                {
                    Content = httpContent
                };
                HttpResponseMessage response = await _httpClient.SendAsync(request);
                //response.EnsureSuccessStatusCode();
                return await response.Content.ReadAsStringAsync();
            }
            catch (Exception ex)
            {
                string Exception = ex.ToString();
                var ExceptionSubstring = Exception.Substring(0, 1500);
                throw new Exception(ExceptionSubstring);
            }
        }

        // DELETE: get id
        public async Task<string> DeleteAsync(string endpoint, string id)
        {
            try
            {
                // Append the ID to the endpoint
                var fullEndpoint = Path.Combine(endpoint, id);

                HttpResponseMessage response = await _httpClient.DeleteAsync(fullEndpoint);
                //response.EnsureSuccessStatusCode();
                return await response.Content.ReadAsStringAsync();
            }
            catch (Exception ex)
            {
                string Exception = ex.ToString();
                var ExceptionSubstring = Exception.Substring(0, 1500);
                throw new Exception(ExceptionSubstring);
            }
        }

        // POST File (No change needed)
        public async Task<string> PostFileAsync(string endpoint, IFormFile file)
        {
            try
            {
                var multipartContent = new MultipartFormDataContent();
                var streamContent = new StreamContent(file.OpenReadStream());

                multipartContent.Add(streamContent, "file", file.FileName);

                HttpResponseMessage res = await _httpClient.PostAsync(endpoint, multipartContent);

                if (res.IsSuccessStatusCode)
                {
                    string result = await res.Content.ReadAsStringAsync();
                    return result;
                }
                else
                {
                    string result = await res.Content.ReadAsStringAsync();
                    return result;
                }
            }
            catch (Exception ex)
            {
                string Exception = ex.ToString();
                var ExceptionSubstring = Exception.Substring(0, 1500);
                throw new Exception(ExceptionSubstring);
            }
        }
    }
}
