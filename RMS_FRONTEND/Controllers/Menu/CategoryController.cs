using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;
using RMS_FRONTEND.Data;
using RMS_FRONTEND.Data.Menu;

namespace RMS_FRONTEND.Controllers.Menu
{
    public class CategoryController : Controller
    {
        private readonly DummyDbContext _context;

        public CategoryController(DummyDbContext context)
        {
            _context = context;
        }

        // GET: Category
        public async Task<IActionResult> Index()
        {
            return View(await _context.Categories.ToListAsync());
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
        public async Task<IActionResult> Create([Bind("CategoryId,CategoryName,GUID,CreatedAt,UpdatedAt,Active")] CategoryMaster categoryMaster)
        {
            if (ModelState.IsValid)
            {
                _context.Add(categoryMaster);
                await _context.SaveChangesAsync();
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
