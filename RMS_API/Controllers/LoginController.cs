using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Data.SqlClient;
using Newtonsoft.Json.Linq;
using Newtonsoft.Json;
using RMS_API.CustomClass;
using RMS_API.Models;
using System.Data;
using System.Text;

namespace RMS_API.Controllers
{
    [Route("api/User")]
    [ApiController]
    public class LoginController : ControllerBase
    {
        private readonly IJwtAuth _jwtAuth;
        private readonly IDataHandler _dh;

        public LoginController(IJwtAuth jwtAuth, IDataHandler dataHandler)
        {
            _jwtAuth = jwtAuth;
            _dh = dataHandler;
        }

        // POST: api/Login/UserLogin
        [HttpPost("Login")]
        public IActionResult UserLogin([FromBody] LoginModel br)
        {
            try
            {
                SqlParameter[] param =
                {
                 new SqlParameter("@UserEmail", br.UsernameOrEmail),
                 new SqlParameter("@Password", br.Password),
                };
                var result = _dh.ReadDataWithResponse("Usp_Sys_UserLogin", param);
                var jsonResult = JsonConvert.DeserializeObject<ResponseModel>(result);
                if (jsonResult.status == 200)
                {
                    var token = _jwtAuth.GenerateToken(br.UsernameOrEmail, br.GUID);
                    jsonResult.data = new { Token=token};
                    return Ok(jsonResult);
                }
                else
                {

                    return StatusCode(StatusCodes.Status204NoContent);
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
                SqlParameter[] param =
                {
                 new SqlParameter("@UserName", br.Username),
                 new SqlParameter("@UserEmail", br.Email),
                 new SqlParameter("@Password", br.Password),
                 new SqlParameter("@PhoneNumber", br.PhoneNumber),
                 new SqlParameter("@Role",br.Role)
                };
                var result = _dh.ReadDataWithResponse("Usp_IU_UserMaster", param);

                return Ok(result);
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, ex.Message);

            }
        }
       
    }
}
