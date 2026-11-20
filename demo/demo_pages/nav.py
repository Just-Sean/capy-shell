"""Demo-only: a stand-in end-user app declaring nav, so get_nav() has something to
return. The shell renders these in a later feature; here they show the contract.

A real module ships a file just like this — plain data, importing nothing from
capy-shell. `url` is a URL name or path; `icon` is a capy-shell icon; `permission`
(enforced in a later feature) would hide the Admin link from non-staff users.
"""

NAV = [
    {
        "key": "demo:home",
        "label": "Home",
        "url": "/",
        "icon": "house",
        "order": 10,
        "section": "Explore",
    },
    {
        "key": "demo:settings",
        "label": "Settings",
        "url": "/",
        "icon": "settings",
        "order": 20,
        "section": "Explore",
    },
    {
        "key": "demo:profile",
        "label": "Profile",
        "url": "/",
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
