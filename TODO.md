# Pet Health ML Admin Dashboard Fix - Revised Plan ✅

**Issue:** Template filter syntax `|replace:"_":" "` unparsable by Django lexer even with {% load %}

**Revised Approach:** Preprocess breed names in view (cleaner, no custom filters needed)

**Completed:**
- [x] Diagnosed filter loading vs parsing issue
- [x] User approved view preprocessing approach
- [x] Created updated TODO.md

**Remaining:**
- [ ] Step 1: Read analytics/views.py for precise edit location
- [ ] Step 2: Read templates/admin/ml_dashboard.html confirm loop
- [ ] Step 3: Edit views.py - create dataset_stats_display dict with formatted names
- [ ] Step 4: Edit template - use dataset_stats_display, remove pipe filters
- [ ] Step 5: Update TODO.md as final completion
