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
			var menus = JsonConvert.DeserializeObject<IEnumerable<MenuModel>>(responseData)?? Enumerable.Empty<MenuModel>() ;
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
        public async Task<IActionResult> Create()
        {
            var responseData = await _apiCall.GetAsync("Category");
            var categories = JsonConvert.DeserializeObject<IEnumerable<CategoryModel>>(responseData) ?? Enumerable.Empty<CategoryModel>();
            ViewData["CategoryId"] = new SelectList(categories, "CategoryId", "CategoryName");
            return View();
        }

        // POST: Menu/Create
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create([Bind("MenuId,MenuName,Description,Price,CategoryId,IsAvailable")] MenuModel menuModel)
        {
            if (ModelState.IsValid)
            {
               var response = await _apiCall.PostAsync("Menu", menuModel);
                return RedirectToAction(nameof(Index));
            }
           
            return View(menuModel);
        }

        // GET: Menu/Edit/5
        public async Task<IActionResult> Edit(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }
            var menuDetails = await _apiCall.GetAsync("Menu", $"{id}");
            var menuModel = JsonConvert.DeserializeObject<MenuModel>(menuDetails) ?? new MenuModel();
            var responseData = await _apiCall.GetAsync("Category");
            var categories = JsonConvert.DeserializeObject<IEnumerable<CategoryModel>>(responseData) ?? Enumerable.Empty<CategoryModel>();
            ViewData["CategoryId"] = new SelectList(categories, "CategoryId", "CategoryName");
            return View(menuModel);
        }

        // POST: Menu/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit([Bind("MenuId,MenuName,Description,Price,CategoryId,IsAvailable")] MenuModel menuModel)
        {
            if (ModelState.IsValid)
            {
                    var response = await _apiCall.PutAsync("Menu", menuModel);
                
                return RedirectToAction(nameof(Index));
            }
            return View(menuModel);
        }

        // GET: Menu/Delete/5
        public async Task<IActionResult> Delete(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var response = await _apiCall.DeleteAsync("Menu", $"{id}");

            return RedirectToAction(nameof(Index));
        }

    }
}
