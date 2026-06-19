# Errors

- no real issue, but maybe add custom exceptions like DecryptionError


# Bugs

- editing entry leaves QListWidget stale, opening it again reveals old data. new data is saved to file successfully tho. PWEditWindow.destroyed doesnt send signal to reset_list


# Missing

- the entirety of TUI...
- inputting the wrong password on gui doesnt show anything, just doesnt process. should color the password box red or shake it or indicate wrong password in some way
- gui styling in general
- maybe add escape to exit window ??
