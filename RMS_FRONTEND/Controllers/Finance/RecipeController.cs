using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;
using Newtonsoft.Json;
using RMS_FRONTEND.Classes;
using RMS_FRONTEND.Models.Finance;
using RMS_FRONTEND.Models.Menu;
using RMS_FRONTEND.Models.Users;

namespace RMS_FRONTEND.Controllers.Finance
{
    public class RecipeController : Controller
    {
        private readonly IApiCall _apiCall;

        public RecipeController(IApiCall apiCall)
        {
            _apiCall = apiCall;
        }

        // GET: Recipe
        public async Task<IActionResult> Index()
        {
			var responseData = await _apiCall.GetAsync("Recipe");
			var recipe = JsonConvert.DeserializeObject<IEnumerable<RecipeData>>(responseData);
            return View(recipe);
		}

        // GET: Recipe/Details/5
        public async Task<IActionResult> Details(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var recipeMaster = await _apiCall.GetAsync("Recipe/", $"{id}");
            var recipeModel = JsonConvert.DeserializeObject<RecipeModel>(recipeMaster);
            return View(recipeModel);
        }

        // GET: Recipe/Create
        public async Task<IActionResult> Create()
        {
            var inventoryData = await _apiCall.GetAsync("Inventory");
            var inventories = JsonConvert.DeserializeObject<IEnumerable<InventoryModel>>(inventoryData);
            ViewData["InventoryId"] = new SelectList(inventories, "InventoryId", "ItemName");

            var responseData = await _apiCall.GetAsync("Menu");
            var menus = JsonConvert.DeserializeObject<IEnumerable<MenuModel>>(responseData) ?? Enumerable.Empty<MenuModel>();
            ViewData["MenuId"] = new SelectList(menus, "MenuId", "MenuName");
            return View();
        }

        // POST: Recipe/Create
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create([FromForm] RecipeModelWithMenu recipe)
        {
            if (ModelState.IsValid)
            {
                var responseData = await _apiCall.PostAsync("Recipe",recipe);
                var recipes = JsonConvert.DeserializeObject<RecipeModel>(responseData);
                return RedirectToAction(nameof(Index));
            }
            return View(recipe);
        }

        // GET: Recipe/Edit/5
        public async Task<IActionResult> Edit(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }

            var inventoryData = await _apiCall.GetAsync("Inventory");
            var inventories = JsonConvert.DeserializeObject<IEnumerable<InventoryModel>>(inventoryData);
            ViewData["InventoryId"] = new SelectList(inventories, "InventoryId", "InventoryId");

            var responseData = await _apiCall.GetAsync("Menu");
            var menus = JsonConvert.DeserializeObject<IEnumerable<MenuModel>>(responseData) ?? Enumerable.Empty<MenuModel>();
            ViewData["MenuId"] = new SelectList(menus, "MenuId", "MenuName");

            var recipeData = await _apiCall.GetAsync("Recipe", $"{id}");
            var recipeModel = JsonConvert.DeserializeObject<RecipeModel>(recipeData);
            return View(recipeModel);
        }

        // POST: Recipe/Edit/5
        // To protect from overposting attacks, enable the specific properties you want to bind to.
        // For more details, see http://go.microsoft.com/fwlink/?LinkId=317598.
        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit(int id, [Bind("RecipeId,MenuId,InventoryId,QuantityRequired")] RecipeModel recipe)
        {
            if (id != recipe.RecipeId)
            {
                return NotFound();
            }

            if (ModelState.IsValid)
            {
                var responseData = await _apiCall.PostAsync("Recipe", recipe);
                var recipes = JsonConvert.DeserializeObject<IEnumerable<RecipeModel>>(responseData);
                return RedirectToAction(nameof(Index));
            }
            return View(recipe);
        }

        // GET: Recipe/Delete/5
        public async Task<IActionResult> Delete(int? id)
        {
            if (id == null)
            {
                return NotFound();
            }
             var recipe = await _apiCall.DeleteAsync("Recipe/",$"{id}");

            return View(recipe);
        }

    }
}
