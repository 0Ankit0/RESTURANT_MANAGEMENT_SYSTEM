using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.DotNet.MSIdentity.Shared;
using Microsoft.EntityFrameworkCore;
using Newtonsoft.Json;
using RMS_FRONTEND.Classes;
using RMS_FRONTEND.Data;
using RMS_FRONTEND.Data.Users;
using RMS_FRONTEND.Models.Users;

namespace RMS_FRONTEND.Controllers.Users
{
    public class UserController : Controller
    {
        private readonly DummyDbContext _context;
        private readonly ICustomFunctions _customFunctions;
        private readonly IApiCall _apiCall;

        public UserController(DummyDbContext context, ICustomFunctions customFunctions,IApiCall apiCall)
        {
            _context = context;
			_customFunctions = customFunctions;
            _apiCall = apiCall;
        }

        // GET: User
        public async Task<IActionResult> Index()
        {
            var responseData = await _apiCall.GetAsync("User");
            var userList = JsonConvert.DeserializeObject<IEnumerable<UserModel>>(responseData);
            return View(userList);
        }

        // GET: User/Details/5
        public async Task<IActionResult> Details(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var userMaster =await _apiCall.GetAsync("User/", $"{id}");
            var userModel = JsonConvert.DeserializeObject<UserModel>(userMaster);
            return View(userModel);
        }

        // GET: User/Create
        public IActionResult Create()
        {
            ViewData["Role"] = _customFunctions.EnumToSelectList<RoleEnum>();
            return View();
        }

        // POST: User/Create
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create([Bind("UserName,UserEmail,Password,Address,Phone,Role,ConfirmPassword")] UserModel userModel)
        {
            if (ModelState.IsValid && userModel.IsValidRole())
            {
                var userMaster = await _apiCall.PostAsync("User/Register",userModel);
                return RedirectToAction(nameof(Index));
            }
            return View(userModel);
        }

        // GET: User/Edit/5
        public async Task<IActionResult> Edit(int? id)
        {
            string response = await _apiCall.GetAsync("User/", $"{id}");
            ViewData["Role"] = _customFunctions.EnumToSelectList<RoleEnum>();
            var userModel = JsonConvert.DeserializeObject<UserModel>(response);
            
            return View(userModel);
        }
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit([Bind("UserId,UserName,UserEmail,Address,Phone,Role")] UserModel userModel)
        {

            string response = await _apiCall.PutAsync("User/Update",userModel);
            return RedirectToAction(nameof(Index));
           
        }

        // GET: User/Delete/5
        public async Task<IActionResult> Delete(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var userMaster = await _apiCall.DeleteAsync("User/Delete", $"{id}");

            return RedirectToAction(nameof(Index));
        }

        // POST: User/Delete/5
        [HttpPost, ActionName("Delete")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> DeleteConfirmed(int id)
        {
            var userMaster = await _context.UserMasters.FindAsync(id);
            if (userMaster != null)
            {
                _context.UserMasters.Remove(userMaster);
            }

            await _context.SaveChangesAsync();
            return RedirectToAction(nameof(Index));
        }

        private bool UserMasterExists(int id)
        {
            return _context.UserMasters.Any(e => e.UserId == id);
        }
    }
}
