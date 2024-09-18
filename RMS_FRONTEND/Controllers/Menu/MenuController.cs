using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;
using Newtonsoft.Json;
using RMS_FRONTEND.Classes;
using RMS_FRONTEND.Data;
using RMS_FRONTEND.Data.Menu;
using RMS_FRONTEND.Models.Menu;
using RMS_FRONTEND.Models.Users;

namespace RMS_FRONTEND.Controllers.Menu
{
    public class MenuController : Controller
    {
        private readonly DummyDbContext _context;
		private readonly IApiCall _apiCall;

		public MenuController(DummyDbContext context,IApiCall apiCall)
        {
            _context = context;
            _apiCall = apiCall;
        }

        // GET: Menu
        public async Task<IActionResult> Index()
        {
			var responseData = await _apiCall.GetAsync("Menu");
			var menus = JsonConvert.DeserializeObject<IEnumerable<MenuModel>>(responseData);
            return View(menus);
		}

        // GET: Menu/Details/5
        public async Task<IActionResult> Details(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var menuMaster = await _context.Menus
                .Include(m => m.Category)
                .FirstOrDefaultAsync(m => m.MenuId == id);
            if (menuMaster == null)
            {
                return NotFound();
            }

            return View(menuMaster);
        }

        // GET: Menu/Create
        public IActionResult Create()
        {
            ViewData["CategoryId"] = new SelectList(_context.Categories, "CategoryId", "CategoryId");
            return View();
        }

        // POST: Menu/Create
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create([Bind("MenuId,MenuName,Description,Price,CategoryId,IsAvailable,GUID,CreatedAt,UpdatedAt,Active")] MenuMaster menuMaster)
        {
            if (ModelState.IsValid)
            {
                _context.Add(menuMaster);
                await _context.SaveChangesAsync();
                return RedirectToAction(nameof(Index));
            }
            ViewData["CategoryId"] = new SelectList(_context.Categories, "CategoryId", "CategoryId", menuMaster.CategoryId);
            return View(menuMaster);
        }

        // GET: Menu/Edit/5
        public async Task<IActionResult> Edit(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var menuMaster = await _context.Menus.FindAsync(id);
            if (menuMaster == null)
            {
                return NotFound();
            }
            ViewData["CategoryId"] = new SelectList(_context.Categories, "CategoryId", "CategoryId", menuMaster.CategoryId);
            return View(menuMaster);
        }

        // POST: Menu/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit(int id, [Bind("MenuId,MenuName,Description,Price,CategoryId,IsAvailable,GUID,CreatedAt,UpdatedAt,Active")] MenuMaster menuMaster)
        {
            if (id != menuMaster.MenuId)
            {
                return NotFound();
            }

            if (ModelState.IsValid)
            {
                try
                {
                    _context.Update(menuMaster);
                    await _context.SaveChangesAsync();
                }
                catch (DbUpdateConcurrencyException)
                {
                    if (!MenuMasterExists(menuMaster.MenuId))
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
            ViewData["CategoryId"] = new SelectList(_context.Categories, "CategoryId", "CategoryId", menuMaster.CategoryId);
            return View(menuMaster);
        }

        // GET: Menu/Delete/5
        public async Task<IActionResult> Delete(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var menuMaster = await _context.Menus
                .Include(m => m.Category)
                .FirstOrDefaultAsync(m => m.MenuId == id);
            if (menuMaster == null)
            {
                return NotFound();
            }

            return View(menuMaster);
        }

        // POST: Menu/Delete/5
        [HttpPost, ActionName("Delete")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> DeleteConfirmed(int id)
        {
            var menuMaster = await _context.Menus.FindAsync(id);
            if (menuMaster != null)
            {
                _context.Menus.Remove(menuMaster);
            }

            await _context.SaveChangesAsync();
            return RedirectToAction(nameof(Index));
        }

        private bool MenuMasterExists(int id)
        {
            return _context.Menus.Any(e => e.MenuId == id);
        }
    }
}
