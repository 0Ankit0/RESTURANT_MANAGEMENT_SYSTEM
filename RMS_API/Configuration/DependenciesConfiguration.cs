using Microsoft.AspNetCore.Identity;
using RMS_API.CustomClass;
using RMS_API.Data.Users;
using RMS_API.Models;
using System.Collections.Concurrent;

namespace RMS_API.Configuration
{
    public class DependenciesConfiguration
    {
        private readonly IConfiguration _configuration;

        public DependenciesConfiguration(IConfiguration configuration)
        {
            _configuration = configuration;
        }

        public void Configureservices(IServiceCollection services)
        {
            //Add the custom AsymmetricCryptography as transient
            services.AddSingleton<ICustomCryptography, AssymetricCryptography>();

            //Add a dictionary as a singleton to map the connection id with the token in hub
            services.AddSingleton(new ConcurrentDictionary<string, MapToHubId>());

            services.AddScoped<IPasswordHasher<UserMaster>, PasswordHasher<UserMaster>>();

            //Add imemoryCache along with memory cache
            services.AddMemoryCache();
            services.AddScoped<ICustomMemoryCache, CustomMemoryCache>();


            //Add datahandler as transient
            services.AddTransient<IDataHandler>(ServiceProvider =>
            {
                // Read the connection string
                var connectionString = _configuration.GetConnectionString("BaseAddress");
                return new DatabaseHelper(connectionString);
            });
        }
    }
}
