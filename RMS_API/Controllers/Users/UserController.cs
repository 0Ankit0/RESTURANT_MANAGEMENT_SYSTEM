using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using RMS_API.CustomClass;
using RMS_API.Data;
using RMS_API.Data.Users;
using RMS_API.Models;
using RMS_API.Models.Users;
using System.Data;

namespace RMS_API.Controllers.Users
{
    [Route("api/[controller]")]
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
        [Authorize]
        public async Task<ActionResult<IEnumerable<UserModel>>> Get()
        {
            try
            {
                var users = await _context.UserMasters
                    .Where(u => u.Active == true)
                    .Select(u => new UserModel
                    {
                        UserId = u.UserId,
                        UserName = u.UserName,
                        UserEmail = u.UserEmail,
                        Phone = u.Phone,
                        Address = u.Address,
                        GUID = u.GUID,
                        Role = u.Role
                    })
                    .ToListAsync();

                return Ok(users);
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, $"Internal server error: {ex.Message}");
            }
        }
        [HttpGet("{id}")]
        [Authorize]
        public async Task<ActionResult<IEnumerable<UserModel>>> Get(int id)
        {
            try
            {
                var users = await _context.UserMasters
                    .Where(u => u.Active == true && u.UserId==id)
                    .Select(u => new UserModel
                    {
                        UserId = u.UserId,
                        UserName = u.UserName,
                        UserEmail = u.UserEmail,
                        Address=u.Address,
                        Phone = u.Phone,
                        GUID = u.GUID,
                        Role = u.Role
                    })
                    .FirstOrDefaultAsync();
                if(users is not null)
                {
                return Ok(users);
                }
                else
                {
                    return NotFound();
                }
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, $"Internal server error: {ex.Message}");
            }
        }

        // POST: api/Login/UserLogin
        [HttpPost("Login")]
        public IActionResult UserLogin([Bind("User")] LoginModel br)
        {
            try
            {
                var user = _context.UserMasters
                           .Where(u => u.Active == true)
                           .FirstOrDefault(u => u.UserEmail == br.UsernameOrEmail);
                if (user == null)
                {
                    return StatusCode(StatusCodes.Status404NotFound, "Invalid email or password.");
                }
                var isValid = _passwordHasher.VerifyHashedPassword(user, user.Password, br.Password);
                if (isValid == PasswordVerificationResult.Success)
                {
                    var token = _jwtAuth.GenerateToken(user.UserEmail, user.Role.ToString(),user.UserId.ToString());
                    var response = new ResponseModel
                    {
                        status = 200,
                        TokenNo = token,
                        Role = user.Role,
                        data = new { }
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
        public IActionResult RegisterUser([FromBody] UserModel br)
        {
            try
            {
                var existingUser = _context.UserMasters.FirstOrDefault(u => u.UserEmail == br.UserEmail);
                if (existingUser != null)
                {
                    return Conflict("User with this email already exists.");
                }
                if(!br.IsValidRole())
                {
                    return BadRequest("Invalid role.");
                }

                // Create a new UserMaster entity
                var user = new UserMaster
                {
                    UserName = br.UserName,
                    UserEmail = br.UserEmail,
                    Password = _passwordHasher.HashPassword(null, br.Password),
                    Phone = br.Phone,
                    Address = br.Address,
                    Role = br.Role,
                    CreatedAt = DateTime.Now,
                    GUID = Guid.NewGuid().ToString(),
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
        [Authorize]
        public IActionResult Put([Bind("UserId,UserName,UserEmail,Phone,Address,Role")] UserModel user)
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
                existingUser.Address = user.Address;
                existingUser.Role = user.Role;
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
        [Authorize]
        public IActionResult Delete(int id)
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

    }
}
