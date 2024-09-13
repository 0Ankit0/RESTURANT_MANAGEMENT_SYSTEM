using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;
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

        public UserController(DummyDbContext context, ICustomFunctions customFunctions)
        {
            _context = context;
			_customFunctions = customFunctions;
        }

        // GET: User
        public async Task<IActionResult> Index()
        {
            var dummyDbContext = _context.UserMasters.Include(u => u.Role);
            return View(await dummyDbContext.ToListAsync());
        }

        // GET: User/Details/5
        public async Task<IActionResult> Details(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var userMaster = await _context.UserMasters
                .Include(u => u.Role)
                .FirstOrDefaultAsync(m => m.UserId == id);
            if (userMaster == null)
            {
                return NotFound();
            }

            return View(userMaster);
        }

        // GET: User/Create
        public IActionResult Create()
        {
            ViewData["RoleId"] = new SelectList(_context.RoleMasters, "RoleId", "RoleId");
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
            ViewData["Role"] = new SelectList(_context.RoleMasters, "Role", "Role", userModel.Role);
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
            ViewData["RoleId"] = new SelectList(_context.RoleMasters, "RoleId", "RoleId", userMaster.RoleId);
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

            var userMaster = await _context.UserMasters
                .Include(u => u.Role)
                .FirstOrDefaultAsync(m => m.UserId == id);
            if (userMaster == null)
            {
                return NotFound();
            }

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
