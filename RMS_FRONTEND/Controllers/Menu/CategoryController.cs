using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;
using Newtonsoft.Json;
using RMS_FRONTEND.Classes;
using RMS_FRONTEND.Models.Menu;
using RMS_FRONTEND.Models.Orders;
using RMS_FRONTEND.Models.Users;

namespace RMS_FRONTEND.Controllers.Menu
{
    public class CategoryController : Controller
    {
		private readonly IApiCall _apiCall;

		public CategoryController(IApiCall apiCall)
        {
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

            var responseData = await _apiCall.GetAsync("Category",$"{id}");
            var categoryMaster = JsonConvert.DeserializeObject<CategoryModel>(responseData);
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

            var categoryMaster = await _apiCall.GetAsync("Category", $"{id}");
			if (categoryMaster == null)
            {
                return NotFound();
            }
            var category = JsonConvert.DeserializeObject<CategoryModel>(categoryMaster);
            return View(category);
        }

        // POST: Category/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit([Bind("CategoryId,CategoryName")] CategoryModel categoryMaster)
        {
           

            if (ModelState.IsValid)
            {
               var response = await _apiCall.PutAsync("Category", categoryMaster);
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

            var responseData = await _apiCall.GetAsync("Category/",$"{id}");
            var categoryMaster = JsonConvert.DeserializeObject<CategoryModel>(responseData);
            return View(categoryMaster);
        }

        
    }
}
