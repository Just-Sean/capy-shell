"""Demo-only: a stand-in end-user app declaring nav, collected and rendered by the
shell. A real module ships a file just like this — plain data, importing nothing from
capy-shell. `url` is a URL name (reversed) or a path; an item with `children` is a group
(a dropdown on the wide top-nav, a collapsible accordion in the sidebar/drawer). Sub-item
links marked `"#"` are placeholders just to show the menu behavior. `permission` hides an
item (the Admin entry shows for a superuser, hidden when logged out).
"""

NAV = [
    {
        "key": "home",
        "label": "Home",
        "url": "home",
        "icon": "house",
        "order": 10,
        "section": "Explore",
    },
    {
        "key": "browse",
        "label": "Browse",
        "order": 20,
        "section": "Explore",
        "children": [
            {"key": "browse:new", "label": "New", "url": "#"},
            {"key": "browse:popular", "label": "Popular", "url": "#"},
            {"key": "browse:all", "label": "Everything", "url": "#"},
        ],
    },
    {
        "key": "library",
        "label": "Library",
        "order": 30,
        "section": "Explore",
        "children": [
            {"key": "lib:books", "label": "Books", "url": "#"},
            {"key": "lib:articles", "label": "Articles", "url": "#"},
            {"key": "lib:videos", "label": "Videos", "url": "#"},
        ],
    },
    {"key": "help", "label": "Help", "url": "#", "order": 40, "section": "Explore"},
    {
        "key": "profile",
        "label": "Profile",
        "url": "demo_profile",
        "icon": "user",
        "order": 10,
        "section": "You",
    },
    {
        "key": "settings",
        "label": "Settings",
        "url": "demo_settings",
        "icon": "settings",
        "order": 20,
        "section": "You",
    },
    {
        "key": "account",
        "label": "Account",
        "icon": "user",
        "order": 30,
        "section": "You",
        "children": [
            {"key": "acct:billing", "label": "Billing", "url": "#"},
            {"key": "acct:security", "label": "Security", "url": "#"},
            {"key": "acct:notifications", "label": "Notifications", "url": "#"},
        ],
    },
    {
        "key": "admin",
        "label": "Admin",
        "url": "admin:index",
        "icon": "external-link",
        "order": 100,
        "section": "You",
        "permission": "demo.view_admin",
    },
]
