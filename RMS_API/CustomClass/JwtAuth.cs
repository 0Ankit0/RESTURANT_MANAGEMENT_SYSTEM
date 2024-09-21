﻿using System;
using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using Microsoft.Extensions.Options;
using System.Text;
using RMS_API.Models;
using Microsoft.IdentityModel.Tokens;
using System.Numerics;

namespace RMS_API.CustomClass
{
     public interface IJwtAuth
    {
        string GenerateToken(string username, string Role, string UserId);
    }

    public class JwtAuth : IJwtAuth
    {
        private readonly JwtSettings _jwtSettings;
        private readonly SymmetricSecurityKey _signingKey;

        public JwtAuth(IOptions<JwtSettings> jwtSettings)
        {
            _jwtSettings = jwtSettings.Value;
            _signingKey = new SymmetricSecurityKey(Encoding.ASCII.GetBytes(_jwtSettings.SecretKey));
        }

        public string GenerateToken(string username, string Role,string UserId)
        {
            var tokenHandler = new JwtSecurityTokenHandler();
            var tokenDescriptor = new SecurityTokenDescriptor
            {
                Subject = new ClaimsIdentity(new[]
                {
                    new Claim(ClaimTypes.Name, username),
                    new Claim(ClaimTypes.Role, Role),
                    new Claim(ClaimTypes.NameIdentifier,UserId),
                    // Add more claims here as needed
                }),
                Expires = DateTime.UtcNow.AddHours(_jwtSettings.TokenLifetimeHours), // Assuming TokenLifetimeHours is a property in JwtSettings
                Issuer = _jwtSettings.Issuer,
                Audience = _jwtSettings.Audience,
                SigningCredentials = new SigningCredentials(_signingKey, SecurityAlgorithms.HmacSha256Signature)
            };

            var token = tokenHandler.CreateToken(tokenDescriptor);
            return tokenHandler.WriteToken(token);
        }
    }
}