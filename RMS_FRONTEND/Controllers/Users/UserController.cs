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
        public async Task<IActionResult> Create([Bind("UserId,UserName,UserEmail,Password,Address,Phone,Role,ConfirmPassword")] UserModel userModel)
        {
            if (ModelState.IsValid)
            {
                UserMaster userMaster = new UserMaster();
                _customFunctions.MapProperties(userModel, userMaster);
                userMaster.GUID = Guid.NewGuid().ToString();
				userMaster.CreatedAt = DateTime.Now;
				_context.Add(userMaster);
                await _context.SaveChangesAsync();
                return RedirectToAction(nameof(Index));
            }
            ViewData["Role"] = _customFunctions.EnumToSelectList<RoleEnum>();
            return View(userModel);
        }

        // GET: User/Edit/5
        public async Task<IActionResult> Edit(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var userMaster = await _context.UserMasters.FindAsync(id);
            if (userMaster == null)
            {
                return NotFound();
            }
            ViewData["Role"] = _customFunctions.EnumToSelectList<RoleEnum>();
            UserModel userModel = new UserModel();
            _customFunctions.MapProperties(userMaster, userModel);
            return View(userModel);
        }

        // POST: User/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit(int id, [Bind("UserName,UserEmail,Address,Phone")] UserModel userModel)
        {
            
            try
            {
                var userMaster = _context.UserMasters.Find(id);
                if(userMaster == null)
                {
                    return NotFound();
                }
                userMaster.UserName = userModel.UserName;
                userMaster.UserEmail = userModel.UserEmail;
                userMaster.Address = userModel.Address;
                userMaster.Phone = userModel.Phone;
                userMaster.UpdatedAt = DateTime.Now;
                _context.Update(userMaster);
                await _context.SaveChangesAsync();
            }
            catch (DbUpdateConcurrencyException)
            {
                if (!UserMasterExists(id))
                {
                    return NotFound();
                }
                else
                {
                    throw;
                }
            }
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

            return View(userMaster);
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
