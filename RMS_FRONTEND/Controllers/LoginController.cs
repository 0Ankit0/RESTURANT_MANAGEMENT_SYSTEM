using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using RMS_FRONTEND.Models;
using System.Reflection;
using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using RMS_FRONTEND.Classes;
using Newtonsoft.Json;

namespace RMS_FRONTEND.Controllers
{
    public class LoginController : Controller
    {
        private static _2FAAuth _2FA;
        private readonly IApiCall _apiCall;

        public LoginController(_2FAAuth _2FAAuth,IApiCall apiCall)
        {
            _2FA = _2FAAuth;
            _apiCall = apiCall;
        }
        // GET: LoginController
        public ActionResult Index(string ReturnUrl)
        {
            if (!string.IsNullOrEmpty(ReturnUrl))
            {
                ModelState.AddModelError("UsernameOrEmail", "You need to login first");
                return View(model: new LoginModel());
            }
            else
            {

            return View();
            }
        }
        [Authorize(Policy = "AdminPolicy")]
         public ActionResult GetQR()
        {
            var name = User.FindFirst(ClaimTypes.Name).Value;
            return StatusCode(StatusCodes.Status200OK,_2FA.GenerateUri(name));
        }

        // GET: LoginController/Details/5
        public ActionResult Details(int id)
        {
            return View();
        }

        // GET: LoginController/Create
        public ActionResult Create()
        {
            return View();
        }

        // POST: LoginController/Create
        [HttpPost]
        [ValidateAntiForgeryToken]
        public ActionResult Create(IFormCollection collection)
        {
            try
            {
                return RedirectToAction(nameof(Index));
            }
            catch
            {
                return View();
            }
        }
        // POST: LoginController/UserLogin
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> UserLogin([FromForm] LoginModel model)
        {
            try
            {
                if (ModelState.IsValid)
                {
                    var loginResponse = await _apiCall.PostAsync("User/Login", model);
                    if (String.IsNullOrEmpty(loginResponse))
                    {
                        ModelState.AddModelError("UsernameOrEmail", "Some error Occured.Please Try Again");
                        return View(nameof(Index), model);
                    }
                        var responseModel = JsonConvert.DeserializeObject<ResponseModel>(loginResponse);
                        if(responseModel.status == 200)
                        {
                        var claims = new List<Claim>
                            {
                                new Claim(ClaimTypes.Name, model.UsernameOrEmail),
                                new Claim(ClaimTypes.Authentication, responseModel.TokenNo),
                                new Claim(ClaimTypes.Role, responseModel.Role)
                            };

                            var claimsIdentity = new ClaimsIdentity(claims, CookieAuthenticationDefaults.AuthenticationScheme);

                            var authProperties = new AuthenticationProperties
                            {
                                /*  If IsPersistent is set to true, the authentication cookie will persist even after the browser is closed. 
                                    If it's false, the authentication cookie will be deleted when the browser is closed.
                                    This is often used to implement "Remember Me" functionality in login forms.*/
                                IsPersistent = true
                            };

                            await HttpContext.SignInAsync(
                                CookieAuthenticationDefaults.AuthenticationScheme,
                                new ClaimsPrincipal(claimsIdentity),
                                authProperties);
                            return RedirectToAction("Index", "Dashboard");
                       
                    }
                    else
                    {
                        ModelState.AddModelError("UsernameOrEmail", "Invalid email or password.");
                        return View("Index", model);
                    }
                }
                else
                {
                    return View("Index", model);
                }
            }
            catch(Exception ex)
            {
                ModelState.AddModelError("",ex.ToString());
                return View(nameof(Index));
            }
        }

        [AutoValidateAntiforgeryToken]
        //[Authorize(Roles ="Admin")]
        [Authorize(Policy ="AdminPolicy")]
        [HttpGet]
        // GET: LoginController/Edit/5
        public ActionResult Edit(int id)
        {
            return View();
        }

        // POST: LoginController/Logout
        [HttpGet]
        [AutoValidateAntiforgeryToken]
        [Authorize(Policy = "AdminPolicy")]
        public async Task<IActionResult> Logout()
        {
            await HttpContext.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
            return RedirectToAction("Index", "Login");
        }


        // GET: LoginController/Delete/5
        public ActionResult Delete(int id)
        {
            return View();
        }

        // POST: LoginController/Delete/5
        [HttpPost]
        [ValidateAntiForgeryToken]
        public ActionResult Delete(int id, IFormCollection collection)
        {
            try
            {
                return RedirectToAction(nameof(Index));
            }
            catch
            {
                return View();
            }
        }
    }
}
