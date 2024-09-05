﻿using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Data.SqlClient;
using Newtonsoft.Json.Linq;
using Newtonsoft.Json;
using RMS_API.CustomClass;
using RMS_API.Models;
using System.Data;
using System.Text;
using RMS_API.Data;
using RMS_API.Data.Users;
using RMS_API.Models.Users;
using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Identity;

namespace RMS_API.Controllers.Users
{
    [Route("api/User")]
    [ApiController]
    public class UserController : ControllerBase
    {
        private readonly IJwtAuth _jwtAuth;
        private readonly IDataHandler _dh;
        private readonly ApplicationDbContext _context;
        private readonly IPasswordHasher<UserMaster> _passwordHasher;


        public UserController(IJwtAuth jwtAuth, IDataHandler dataHandler, ApplicationDbContext context, IPasswordHasher<UserMaster> passwordHasher)
        {
            _jwtAuth = jwtAuth;
            _dh = dataHandler;
            _context = context;
            _passwordHasher = passwordHasher;
        }
        [HttpGet]
        public async Task<ActionResult<IEnumerable<UserModel>>> Get()
        {
            try
            {
                var users = await _context.UserMasters
                .Include(u => u.UserRoles)
                .ThenInclude(ur => ur.Role)
                .Select(u => new UserModel
                {
                    UserId = u.UserId,
                    UserName = u.UserName,
                    UserEmail = u.UserEmail,
                    Phone = u.Phone,
                    GUID = u.GUID,
                    Role = u.UserRoles.Where(ur => ur.UserId == u.UserId)
                          .Select(ur => ur.Role.RoleName)
                          .FirstOrDefault() ?? string.Empty
                })
                .ToListAsync();

                return Ok(users);
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, $"Internal server error: {ex.Message}");
            }
        }

        [HttpPost("Role")]
        public async Task<IActionResult> Post([FromBody] UserRoleModel userRole)
        {
            try
            {
                UserRole role = new UserRole()
                {
                    UserId=userRole.UserId,
                    RoleId = userRole.RoleId,
                    CreatedAt = DateTime.Now,
                    GUID = Guid.NewGuid().ToString()
                };
                await _context.UserRoles.AddAsync(role);
                await _context.SaveChangesAsync();
                return Ok(role);
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, $"Internal server error: {ex.Message}");
            }
        }
        // POST: api/Login/UserLogin
        [HttpPost("Login")]
        public IActionResult UserLogin([FromBody] LoginModel br)
        {
            try
            {
                var user = _context.UserMasters
                           .FirstOrDefault(u => u.UserEmail == br.UsernameOrEmail);
                var isValid = _passwordHasher.VerifyHashedPassword(user, user.Password, br.Password);
                if (isValid == PasswordVerificationResult.Success)
                {
                    var token = _jwtAuth.GenerateToken(user.UserEmail, user.GUID);
                    var response = new ResponseModel
                    {
                        status = 200,
                        data = new { Token = token }
                    };
                    return Ok(response);
                }
                else
                {
                    var res = new ResponseModel
                    {
                        status = 204,
                        message = "Invalid email or password."
                    };
                    return StatusCode(StatusCodes.Status404NotFound, res);
                }

            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, ex.Message);

            }
        }

        // POST: api/Login/Register
        [HttpPost("Register")]
        public IActionResult RegisterUser([FromBody] RegisterModel br)
        {
            try
            {
                var existingUser = _context.UserMasters.FirstOrDefault(u => u.UserEmail == br.Email);
                if (existingUser != null)
                {
                    return Conflict("User with this email already exists.");
                }

                // Find the role by name (assuming you have a method or logic to retrieve the role)
                var role = _context.RoleMasters.FirstOrDefault(r => r.RoleId == br.Role);
                if (role == null)
                {
                    return BadRequest("Invalid role specified.");
                }

                // Create a new UserMaster entity
                var user = new UserMaster
                {
                    UserName = br.Username,
                    UserEmail = br.Email,
                    Password = _passwordHasher.HashPassword(null, br.Password) ,
                    Phone = br.PhoneNumber,
                    RoleId = role.RoleId, // Set the RoleId
                    CreatedAt = DateTime.Now,
                    //GUID = Guid.NewGuid().ToString(),
                    Active = true
                };

                // Add the user to the database
                _context.UserMasters.Add(user);
                _context.SaveChanges();

                // Return a success response
                return Ok("User registered successfully.");
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, ex.Message);

            }
        }

        [HttpPut("Update")]
        public IActionResult UpdateUser([FromBody] UserMaster user)
        {
            try
            {
                var existingUser = _context.UserMasters.FirstOrDefault(u => u.UserId == user.UserId);
                if (existingUser == null)
                {
                    return NotFound("User not found.");
                }

                existingUser.UserName = user.UserName;
                existingUser.UserEmail = user.UserEmail;
                existingUser.Phone = user.Phone;
                existingUser.RoleId = user.RoleId;
                existingUser.UpdatedAt = DateTime.Now;

                _context.SaveChanges();

                return Ok("User updated successfully.");
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, ex.Message);
            }
        }

        [HttpDelete("Delete/{id}")]
        public IActionResult DeleteUser(int id)
        {
            try
            {
                var user = _context.UserMasters.FirstOrDefault(u => u.UserId == id);
                if (user == null)
                {
                    return NotFound("User not found.");
                }

                //_context.UserMasters.Remove(user);
                user.Active = false;
                _context.SaveChanges();

                return Ok("User deleted successfully.");
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, ex.Message);
            }
        }
    [HttpDelete("Role/{id}")]
        public IActionResult DeleteUserRole(int id)
        {
            try
            {
                var user = _context.UserMasters.FirstOrDefault(u => u.UserId == id);
                if (user == null)
                {
                    return NotFound("User not found.");
                }

                //_context.UserMasters.Remove(user);
                user.RoleId = null;
                _context.SaveChanges();

                return Ok("User's role removed successfully.");
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, ex.Message);
            }
        }
    
    
    }
}
