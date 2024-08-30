using Asp.Versioning;
using Asp.Versioning.ApiExplorer;
using Microsoft.OpenApi.Models;

namespace RMS_API.Configuration
{
    public class SwaggerConfiguration
    {
        private readonly IConfiguration _configuration;

        public SwaggerConfiguration(IConfiguration configuration)
        {
            _configuration = configuration;
        }
        public void ConfigureServices(IServiceCollection services)
        {

            // Configure API versioning  more info https://dev.to/azzdcl/aspnet-core-web-api-with-swagger-api-versioning-for-dotnet-8-3c9j
            services.AddApiVersioning(options =>
            {
                options.AssumeDefaultVersionWhenUnspecified = true; // Assumes the default version if none is specified
                options.DefaultApiVersion = new ApiVersion(1, 0);   // Set the default API version to 1.0
                options.ReportApiVersions = true;
                //options.ApiVersionReader = ApiVersionReader.Combine(
                //new UrlSegmentApiVersionReader(),  //reads the API version from a segment in the URL path.
                //new QueryStringApiVersionReader("api-version"), //this is for query parameter based versioning
                //new HeaderApiVersionReader("X-Version"), //allows clients to specify the API version in a custom HTTP header. 
                //new MediaTypeApiVersionReader("ver"));//allows clients to specify the API version in the Content-Type or Accept HTTP headers by including a version parameter. 
            })
                .AddApiExplorer(
                options =>
                {
                    options.GroupNameFormat = "'v'VVV";
                    options.SubstituteApiVersionInUrl = true;
                });

            // Add Swagger and configure SwaggerGen
            services.AddEndpointsApiExplorer();
            services.AddSwaggerGen(options =>
            {
                // Use the IServiceProvider to resolve IApiVersionDescriptionProvider
                var serviceProvider = services.BuildServiceProvider();
                var apiVersionDescriptionProvider = serviceProvider.GetRequiredService<IApiVersionDescriptionProvider>();

                foreach (var description in apiVersionDescriptionProvider.ApiVersionDescriptions)
                {
                    options.SwaggerDoc(description.GroupName, CreateInfoForApiVersion(description));
                }
            });
        }
        private OpenApiInfo CreateInfoForApiVersion(ApiVersionDescription description)
        {
            var info = new OpenApiInfo
            {
                Title = "API Title",
                Version = description.ApiVersion.ToString(),
                Description = $"API Description for version {description.ApiVersion}"
            };

            return info;
        }
    }
}