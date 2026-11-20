"""Demo-only: a stand-in end-user app declaring nav, collected and rendered by the
shell. A real module ships a file just like this — plain data, importing nothing from
capy-shell. `url` is a URL name (reversed) or a path; `icon` is a capy-shell icon;
`permission` hides the entry from users without it (the Admin entry shows for a
superuser, who has every permission, and is hidden when logged out).
"""

NAV = [
    {
        "key": "demo:home",
        "label": "Home",
        "url": "home",
        "icon": "house",
        "order": 10,
        "section": "Explore",
    },
    {
        "key": "demo:settings",
        "label": "Settings",
        "url": "demo_settings",
        "icon": "settings",
        "order": 20,
        "section": "Explore",
    },
    {
        "key": "demo:profile",
        "label": "Profile",
        "url": "demo_profile",
        "icon": "user",
        "order": 10,
        "section": "You",
    },
    {
        "key": "demo:admin",
        "label": "Admin",
        "url": "admin:index",
        "icon": "external-link",
        "order": 100,
        "section": "You",
        "permission": "demo.view_admin",
    },
]
