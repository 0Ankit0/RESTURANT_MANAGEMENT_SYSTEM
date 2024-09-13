using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;
using RMS_FRONTEND.Data;
using RMS_FRONTEND.Data.Users;

namespace RMS_FRONTEND.Controllers.Users
{
    public class RoleController : Controller
    {
        private readonly DummyDbContext _context;

        public RoleController(DummyDbContext context)
        {
            _context = context;
        }

        // GET: Role
        public async Task<IActionResult> Index()
        {
            return View(await _context.RoleMasters.ToListAsync());
        }

        // GET: Role/Details/5
        public async Task<IActionResult> Details(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var roleMaster = await _context.RoleMasters
                .FirstOrDefaultAsync(m => m.RoleId == id);
            if (roleMaster == null)
            {
                return NotFound();
            }

            return View(roleMaster);
        }

        // GET: Role/Create
        public IActionResult Create()
        {
            return View();
        }

        // POST: Role/Create
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create([Bind("RoleId,RoleName,GUID,CreatedAt,UpdatedAt,Active")] RoleMaster roleMaster)
        {
            if (ModelState.IsValid)
            {
                _context.Add(roleMaster);
                await _context.SaveChangesAsync();
                return RedirectToAction(nameof(Index));
            }
            return View(roleMaster);
        }

        // GET: Role/Edit/5
        public async Task<IActionResult> Edit(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var roleMaster = await _context.RoleMasters.FindAsync(id);
            if (roleMaster == null)
            {
                return NotFound();
            }
            return View(roleMaster);
        }

        // POST: Role/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit(int id, [Bind("RoleId,RoleName,GUID,CreatedAt,UpdatedAt,Active")] RoleMaster roleMaster)
        {
            if (id != roleMaster.RoleId)
            {
                return NotFound();
            }

            if (ModelState.IsValid)
            {
                try
                {
                    _context.Update(roleMaster);
                    await _context.SaveChangesAsync();
                }
                catch (DbUpdateConcurrencyException)
                {
                    if (!RoleMasterExists(roleMaster.RoleId))
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
            return View(roleMaster);
        }

        // GET: Role/Delete/5
        public async Task<IActionResult> Delete(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var roleMaster = await _context.RoleMasters
                .FirstOrDefaultAsync(m => m.RoleId == id);
            if (roleMaster == null)
            {
                return NotFound();
            }

            return View(roleMaster);
        }

        // POST: Role/Delete/5
        [HttpPost, ActionName("Delete")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> DeleteConfirmed(int id)
        {
            var roleMaster = await _context.RoleMasters.FindAsync(id);
            if (roleMaster != null)
            {
                _context.RoleMasters.Remove(roleMaster);
            }

            await _context.SaveChangesAsync();
            return RedirectToAction(nameof(Index));
        }

        private bool RoleMasterExists(int id)
        {
            return _context.RoleMasters.Any(e => e.RoleId == id);
        }
    }
}
