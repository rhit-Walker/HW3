import socket
import traceback
# Source:https://www.w3schools.com/PYTHON/module_random.asp
import random
from datetime import date
# source: https://docs.python.org/3/library/html.html
from html import escape
# source: https://docs.python.org/3/library/urllib.parse.html
from urllib.parse import unquote_plus

def createGamePage(game):
    with open("./public/game.html", "r", encoding="utf-8") as fd:
        template = fd.read()

    buttons = ""

    for i in range(len(game["lights"])):
        # create correct button
        if game["lights"][i]:
            label = "O"
            buttonClass = "on"
        else:
            label = "X"
            buttonClass = "off"

        buttons += (
            '<button type="submit" name="button_index" '
            + 'value="' + str(i + 1) + '" class="' + buttonClass + '">'
            + label + '</button>\n'
        )

    rendered_page = template.format(
        player_name=escape(game["player_name"]),
        moves=game["moves"],
        buttons=buttons
    )

    return rendered_page.encode("utf-8")


def updateBestScores(game, bestScores):
    numberOfLights = len(game["lights"])
    newBest = False

    if numberOfLights not in bestScores:
        newBest = True
    elif game["moves"] < bestScores[numberOfLights]["moves"]:
        newBest = True

    # Ties keep the earlier score.
    if newBest:
        bestScores[numberOfLights] = {
            "moves": game["moves"],
            "player_name": game["player_name"],
            "date": date.today().strftime("%Y-%m-%d")
        }

    return newBest


def createBestScores(bestScores, message="", newBestSize=None):
    with open("./public/best_scores.html", "r", encoding="utf-8") as fd:
        template = fd.read()

    rows = ""

    for numberOfLights in sorted(bestScores):
        score = bestScores[numberOfLights]
        player_name = escape(score["player_name"])

        if numberOfLights == newBestSize:
            rows += '<tr class="new-best">'
            player_name += " (NEW BEST)"
        else:
            rows += "<tr>"

        rows += f"<td>{numberOfLights}</td>"
        rows += f'<td>{score["moves"]}</td>'
        rows += f"<td>{player_name}</td>"
        rows += f'<td>{score["date"]}</td>'
        rows += "</tr>\n"

    if rows == "":
        rows = '<tr><td colspan="4">No scores yet.</td></tr>'

    createdPage = template.format(
        message=escape(message),
        rows=rows
    )

    return createdPage.encode("utf-8")


def finishGame(game, bestScores):
    newBest = updateBestScores(game, bestScores)
    message = f'You won in {game["moves"]} moves!'
    newBestSize = None

    if newBest:
        message += " New best score!"
        newBestSize = len(game["lights"])

    return createBestScores(bestScores, message, newBestSize)


def createErrorPage(message):
    page = (
        '<!DOCTYPE html>'
        '<html lang="en">'
        '<head>'
        '<meta charset="utf-8">'
        '<title>Error</title>'
        '<link rel="stylesheet" href="/styles.css">'
        '</head>'
        '<body>'
        f'<h1>{escape(message)}</h1>'
        '<p><a href="/startgame.html">Start a new game</a></p>'
        '</body>'
        '</html>'
    )

    return page.encode("utf-8")

def toggleLight(game, buttonIndex):
    lights = game["lights"]

    if buttonIndex < 1 or buttonIndex > len(lights):
        raise ValueError("Invalid button number.")

    # Buttons start at 1.
    i = buttonIndex - 1

    start = max(0, i - 1)
    stop = min(len(lights), i + 2)

    for position in range(start, stop):
        lights[position] = not lights[position]

    game["moves"] += 1

def createGame(formFields):
    numberOfLights = int(formFields["number_of_lights"])
    offLights = int(formFields["off_lights"])
    playerName = formFields["player_name"].strip()
    # handle various errors
    if numberOfLights < 1:
        # Source:https://www.youtube.com/watch?v=V3nqBxllUlI
        raise ValueError("There must be at least 1 light")

    if offLights < 0 or offLights > numberOfLights:
        raise ValueError("Check the number of lights starting off.")

    if playerName == "":
        raise ValueError("Enter a player name.")

    # Lights start on
    lights = [True] * numberOfLights

    offPositions = random.sample(range(numberOfLights), offLights)
    # Randomly select positions for lights that start off
    for position in offPositions:
        lights[position] = False

    game = {
        "lights": lights,
        "player_name": playerName,
        "moves": 0
    }

    return game

def parse_headers(reader_from_browser):
    headers = {}
    while True:
        line = reader_from_browser.readline().decode("utf-8").strip()
        if not line:
            break
        key, value = line.split(":", 1)
        headers[key.strip()] = value.strip()
    return headers


def parse_post_request_form_fields(headers, reader_from_browser):
    content_length = 0
    content_type = ""

    for key, value in headers.items(): # Find content length and type
        # Source for .lower(): https://www.w3schools.com/python/ref_string_lower.asp
        if key.lower() == "content-length":
            content_length = int(value)
        if key.lower() == "content-type":
            content_type = value
    # Read the body of the request (no extra spaces)
    body = reader_from_browser.read(content_length).decode("utf-8").strip()
    form_fields = {}
    # source: https://www.w3schools.com/python/ref_string_startswith.asp
    if content_type.startswith("application/x-www-form-urlencoded"): #urlencoded form data
        fields = body.split("&")
        for field in fields:                                         #seperate each field into key and value
            key, value = field.split("=", 1)
            form_fields[key] = unquote_plus(value)                  #decodes the value from URL encoding
    else:
        # source for splitlines:https://www.w3schools.com/python/ref_string_splitlines.asp
        for line in body.splitlines():                              #text/plain form data
            key, value = line.split("=", 1)
            form_fields[key] = value
    return form_fields


def get_requested_method(request_line):
    parts = request_line.split()
    return parts[0]


def get_requested_filename(request_line):
    parts = request_line.split()
    path = parts[1]
    if not path.startswith("."):
        return "./public" + path
    return path


def get_file_type(file_name):
    return "." + file_name.split(".")[-1]


def get_content_type(file_extension):
    if file_extension in (".html", ".htm"):
        return "text/html; charset=utf-8"
    elif file_extension == ".txt":
        return "text/plain; charset=utf-8"
    elif file_extension in (".jpg", ".jpeg"):
        return "image/jpeg"
    elif file_extension == ".png":
        return "image/png"
    elif file_extension == ".css":
        return "text/css; charset=utf-8"
    elif file_extension == ".ico":
        return "image/x-icon"
    elif file_extension == ".js":
        return "text/javascript; charset=utf-8"
    else:
        return "application/octet-stream"


# This function (and the following) was moved here for clarity,
# but is the same thing we have done in the
# past to handle special routes like /shutdown and getting request bodies
def handle_special_routes(requested_filename, connection_to_browser):
    if requested_filename == "./public/shutdown":
        print("Server shutting down")
        shutdown_connection(connection_to_browser)
        exit()


def get_file_body_in_bytes(requested_filename):
    with open(requested_filename, "rb") as fd:
        return fd.read()





def main(testing_flags=None):
    # Do not change the following code. This is here to allow us to manage part of your server
    # during testing.
    flags = initialize_flags(testing_flags)
    server = create_connection(port=8080)

    currentGame = None
    bestScores = {}

    while flags["continue"]:
        # Wait for the browser to send a HTTP Request
        connection_to_browser = accept_browser_connection_to(server)

        # Read the HTTP Request from the browser
        reader_from_browser = connection_to_browser.makefile(mode="rb")
        try:
            request_line = reader_from_browser.readline().decode("utf-8") # decode converts from bytes to text
            print("\nRequest:")
            print(request_line)
        except Exception as e:
            print("Error while reading HTTP Request:", e)
            traceback.print_exc() # Print what line the server crashed on.
            reader_from_browser.close()
            shutdown_connection(connection_to_browser)
            continue

        if not request_line.strip():
            reader_from_browser.close()
            shutdown_connection(connection_to_browser)
            continue

        # Gets the requested filename, extension, and file type
        requestedFilename = get_requested_filename(request_line)

        if requestedFilename == "./public/":
            requestedFilename = "./public/startgame.html"

        file_extension = get_file_type(requestedFilename)
        content_type = get_content_type(file_extension)

        # DONE: Get the requested HTTP Method
        # Implement a new get_requested_method function, which takes the
        # request line, and then call it here
        requested_method = get_requested_method(request_line)

        # DONE: Print requested method
        print("Requested file:", requestedFilename)
        print("Extension:", file_extension)
        print("Requested method:", requested_method)

        # DONE: Read all Headers into a Dictionary
        # Implement a new parse_headers function, which takes the
        # browser stream (called reader_from_browser),
        # and then call it here
        headers = parse_headers(reader_from_browser)

        # Move handling shutdown to a new function for clarity
        handle_special_routes(requestedFilename, connection_to_browser)

        # Write the HTTP Response back to the browser
        writer_to_browser = connection_to_browser.makefile(mode="wb")
        try:
            status = "200 OK"

            try:
                # DONE: Handle GET and POST requests differently
                # The code below is what we did before to handle GET requests,
                # but it's been partially moved into a function for clarity.
                if requested_method == "POST":
                    form_fields = parse_post_request_form_fields(
                        headers, reader_from_browser
                    )

                    print("Form fields:", form_fields)
                    content_type = "text/html; charset=utf-8"

                    if requestedFilename == "./public/game.html":
                        currentGame = createGame(form_fields)

                        # All lights may already be off.
                        if not any(currentGame["lights"]):
                            responseBody = finishGame(
                                currentGame, bestScores
                            )
                            currentGame = None
                        else:
                            responseBody = createGamePage(currentGame)

                    elif requestedFilename == "./public/toggle_light":
                        if currentGame is None:
                            status = "403 Forbidden"
                            responseBody = createErrorPage("403 Forbidden: No game is in progress.")
                        else:
                            buttonIndex = int(form_fields["button_index"])
                            toggleLight(currentGame, buttonIndex)

                            if not any(currentGame["lights"]):
                                responseBody = finishGame(
                                    currentGame, bestScores
                                )
                                currentGame = None
                            else:
                                responseBody = createGamePage(currentGame)

                    else:
                        status = "404 Not Found"
                        responseBody = createErrorPage("404 server offline")

                elif requested_method == "GET":
                    if requestedFilename == "./public/game.html":
                        if currentGame is None:
                            status = "403 Forbidden"
                            responseBody = createErrorPage("403 Forbidden: No game is in progress.")
                        else:
                            responseBody = createGamePage(currentGame)

                    elif requestedFilename == "./public/best_scores.html":
                        responseBody = createBestScores(bestScores)

                    elif requestedFilename in ("./public/startgame.html","./public/styles.css"):
                        responseBody = get_file_body_in_bytes(requestedFilename)
                    else:
                        status = "404 Not Found"
                        content_type = "text/html; charset=utf-8"
                        responseBody = createErrorPage("404 no touching >:(")


            except (ValueError, KeyError):
                status = "400 Bad Request"
                content_type = "text/html; charset=utf-8"
                responseBody = createErrorPage(
                    "400 Bad Request: Check your form values."
                )

            # DONE: Implement a new function called parse_post_request_form_fields.
            # It should have the following signature:
            #   parse_post_request_form_fields(headers, reader_from_browser)
            #
            # It should return a dictionary of the form fields and their values.
            # Then, call the parse_post_request_form_fields function here to get the
            # form field values.
            # Then print the fields for debugging.

            # TODO: Decide what to do with the data.

            response_headers = "\r\n".join([
                f"HTTP/1.1 {status}",
                f"Content-Type: {content_type}",
                f"Content-length: {len(responseBody)}",
                "Connection: close",
                "\r\n",
            ]).encode("utf-8")

            # These lines just PRINT the HTTP Response to your Terminal.
            print()
            print('Response headers:')
            print(response_headers)
            print()
            print('Response body:')
            print(responseBody)
            print()

            # These lines do the real work; they write the HTTP Response to the Browser.
            writer_to_browser.write(response_headers)
            writer_to_browser.write(responseBody)
            writer_to_browser.flush()
        except Exception as e:
            print("Error while writing HTTP Response:", e)
            flags["exceptions"].append(e)
            traceback.print_exc() # print what line the server crashed on

        writer_to_browser.close()
        reader_from_browser.close()
        shutdown_connection(connection_to_browser)

    server.close()


# Don't worry about the details of the rest of the code below.
# It is VERY low-level code for creating the underlying connection to the browser.

def create_connection(port):
    addr = ("", port) # "" = all network adapters; usually what you want.
    server = socket.create_server(addr, family=socket.AF_INET6, dualstack_ipv6=True) # prevent rare IPV6 softlock on localhost connections
    server.settimeout(2)
    print(f"Server started on port {port}. Try: http://localhost:{port}/startgame.html")
    return server


def accept_browser_connection_to(server):
    while True:
        try:
            (conn, address) = server.accept()
            conn.settimeout(2)
            return conn
        except socket.timeout:
            print(".", end="", flush=True)
        except KeyboardInterrupt:
            exit(0)


def shutdown_connection(connection_to_browser):
    connection_to_browser.shutdown(socket.SHUT_RDWR)
    connection_to_browser.close()


def initialize_flags(testing_flags):
    flags = testing_flags if testing_flags is not None else {}
    if "continue" not in flags:
        flags["continue"] = True
    if "exceptions" not in flags:
        flags["exceptions"] = []
    return flags


if __name__ == "__main__":
    main()