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
    public class CategoryController : Controller
    {
        private readonly DummyDbContext _context;
		private readonly IApiCall _apiCall;

		public CategoryController(DummyDbContext context,IApiCall apiCall)
        {
            _context = context;
            _apiCall = apiCall;
        }

        // GET: Category
        public async Task<IActionResult> Index()
        {
			var responseData = await _apiCall.GetAsync("Category");
			var categories = JsonConvert.DeserializeObject<IEnumerable<CategoryModel>>(responseData);
            return View(categories);
		}

        // GET: Category/Details/5
        public async Task<IActionResult> Details(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var categoryMaster = await _context.Categories
                .FirstOrDefaultAsync(m => m.CategoryId == id);
            if (categoryMaster == null)
            {
                return NotFound();
            }

            return View(categoryMaster);
        }

        // GET: Category/Create
        public IActionResult Create()
        {
            return View();
        }

        // POST: Category/Create
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create([Bind("CategoryName")] CategoryModel categoryMaster)
        {
            if (ModelState.IsValid)
            {
                var responseData = await _apiCall.PostAsync("Category",categoryMaster);
                return RedirectToAction(nameof(Index));
            }
            return View(categoryMaster);
        }

        // GET: Category/Edit/5
        public async Task<IActionResult> Edit(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var categoryMaster = await _context.Categories.FindAsync(id);
            if (categoryMaster == null)
            {
                return NotFound();
            }
            return View(categoryMaster);
        }

        // POST: Category/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit(int id, [Bind("CategoryId,CategoryName,GUID,CreatedAt,UpdatedAt,Active")] CategoryMaster categoryMaster)
        {
            if (id != categoryMaster.CategoryId)
            {
                return NotFound();
            }

            if (ModelState.IsValid)
            {
                try
                {
                    _context.Update(categoryMaster);
                    await _context.SaveChangesAsync();
                }
                catch (DbUpdateConcurrencyException)
                {
                    if (!CategoryMasterExists(categoryMaster.CategoryId))
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
            return View(categoryMaster);
        }

        // GET: Category/Delete/5
        public async Task<IActionResult> Delete(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var categoryMaster = await _context.Categories
                .FirstOrDefaultAsync(m => m.CategoryId == id);
            if (categoryMaster == null)
            {
                return NotFound();
            }

            return View(categoryMaster);
        }

        // POST: Category/Delete/5
        [HttpPost, ActionName("Delete")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> DeleteConfirmed(int id)
        {
            var categoryMaster = await _context.Categories.FindAsync(id);
            if (categoryMaster != null)
            {
                _context.Categories.Remove(categoryMaster);
            }

            await _context.SaveChangesAsync();
            return RedirectToAction(nameof(Index));
        }

        private bool CategoryMasterExists(int id)
        {
            return _context.Categories.Any(e => e.CategoryId == id);
        }
    }
}
