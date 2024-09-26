# ..\Documents\problem-graph\static\index.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Node Graph with Quill Editor</title>
    <style>
        body {
            font-family: Arial, sans-serif;
        }
        h1 {
            text-align: center;
        }
        details {
            margin-left: 20px;
        }
        form {
            margin: 20px 0;
        }
        label {
            display: block;
            margin-top: 10px;
        }
        input[type="text"],
        textarea {
            width: 100%;
            padding: 10px;
            margin-top: 5px;
        }
        button {
            margin-top: 10px;
            padding: 10px 20px;
            background-color: #28a745;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background-color: #218838;
        }
        .node {
            border: 1px solid #ddd;
            padding: 10px;
            margin-bottom: 10px;
            cursor: pointer;  /* Make nodes clickable */
        }
        .node img {
            max-width: 100%;
            height: auto;
        }
        .selected {
            background-color: #f0f8ff;
        }
    </style>

    <!-- Include Quill from CDN -->
    <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
    <script src="https://cdn.quilljs.com/1.3.6/quill.min.js"></script>
    
    <script src="https://unpkg.com/htmx.org"></script>
</head>
<body>

    <h1>Node Graph with Quill Editor</h1>

    <!-- Form to add a new node -->
    <div>
        <form hx-post="/create-node" hx-target="#node-list" hx-swap="beforeend">
            <label>Node Name: <input type="text" name="node_name" required></label>
            <label>Connected Node ID: <input type="text" name="connected_node" id="connected_node" readonly></label>
            
            <!-- Quill Editor for HTML Content -->
            <label>HTML Content:</label>
            <div id="editor-container" style="height: 200px; border: 1px solid #ccc;"></div>
            <input type="hidden" name="html_content" id="html_content">
            
            <input type="hidden" name="author_email" value="">
            <button type="submit">Add Node</button>
        </form>
    </div>

    <!-- Display node list here -->
    <div id="node-list">
        <!-- Dynamically generated content will be inserted here -->
    </div>

    <script>
        // Initialize Quill editor
        var quill = new Quill('#editor-container', {
            theme: 'snow',
            modules: {
                toolbar: [
                    [{ 'header': [1, 2, false] }],
                    ['bold', 'italic', 'underline'],
                    ['image', 'link'],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                    [{ 'align': [] }],
                    ['clean']  // remove formatting button
                ]
            }
        });

        // Ensure that Quill content is stored in the hidden input before form submission
        document.querySelector('form').onsubmit = function() {
            var htmlContent = document.querySelector('input[name=html_content]');
            htmlContent.value = quill.root.innerHTML;  // Set the hidden input value to the Quill editor content
        };

        // Set up the email from local storage or prompt the user
        function getEmail() {
            let email = localStorage.getItem("author_email");
            if (!email) {
                email = prompt("Please enter your email address:");
                if (email) {
                    localStorage.setItem("author_email", email);
                } else {
                    alert("Email is required to proceed.");
                    return null;
                }
            }
            return email;
        }

        // Function to set the parent node ID in the form
        function setParentNode(nodeId) {
            document.getElementById("connected_node").value = nodeId;
        }

        // Function to handle node selection
        function handleNodeSelection(node) {
            // Remove the 'selected' class from any previously selected node
            const previouslySelected = document.querySelector('.node.selected');
            if (previouslySelected) {
                previouslySelected.classList.remove('selected');
            }

            // Add the 'selected' class to the clicked node
            node.classList.add('selected');

            // Set the connected node ID in the form
            const nodeId = node.getAttribute('data-node-id');
            setParentNode(nodeId);
        }

        // Function to add click event listeners to nodes
        function addClickListenersToNodes() {
            const nodes = document.querySelectorAll('.node');
            nodes.forEach(node => {
                node.addEventListener('click', function () {
                    handleNodeSelection(this);  // Handle node selection
                });
            });
        }

        // Function to load existing nodes when the page loads
        document.addEventListener("DOMContentLoaded", function() {
            const email = getEmail();
            if (!email) return;  // Stop execution if email isn't provided

            fetch("/load-nodes")
                .then(response => response.text())
                .then(html => {
                    const nodeList = document.getElementById("node-list");
                    nodeList.innerHTML = html;
                    addClickListenersToNodes();  // Add click listeners to newly rendered nodes
                })
                .catch(error => console.error("Error loading nodes:", error));
        });
    </script>

</body>
</html>

// ..\Documents\problem-graph\database\api.go
package database

import (
	"database/sql"
	"fmt"
	"log"
)

// GetLastInsertedNodeVersionID retrieves the latest node_version_id.
func (g *GraphDB) GetLastInsertedNodeVersionID() (int64, error) {
	log.Println("Getting last inserted node version ID")
	var nodeVersionID int64
	query := `SELECT COALESCE(MAX(node_version_id),0) FROM nodes`
	err := g.db.QueryRow(query).Scan(&nodeVersionID)
	if err != nil {
		log.Printf("Error getting last node_version_id: %v", err)
		return 0, fmt.Errorf("failed to retrieve last node_version_id: %w", err)
	}
	return nodeVersionID, nil
}

// GetLastInsertedEdgeVersionID retrieves the latest edge_version_id.
func (g *GraphDB) GetLastInsertedEdgeVersionID() (int64, error) {
	log.Println("Getting last inserted edge version ID")
	var edgeVersionID int64
	query := `SELECT COALESCE(MAX(edge_version_id),0) FROM edges`
	err := g.db.QueryRow(query).Scan(&edgeVersionID)
	if err != nil {
		return 0, fmt.Errorf("failed to retrieve last edge_version_id: %w", err)
	}
	return edgeVersionID, nil
}

// GetLatestHTMLNode retrieves the html_div content of the latest version of a node.
func (g *GraphDB) GetLatestHTMLNode(nodeVersionID int64) (string, error) {
	if nodeVersionID <= 0 {
		return "", fmt.Errorf("invalid node ID: %d", nodeVersionID)
	}

	var htmlDiv string
	query := `SELECT html_div FROM nodes WHERE node_version_id = ?`
	err := g.db.QueryRow(query, nodeVersionID).Scan(&htmlDiv)
	if err != nil {
		if err == sql.ErrNoRows {
			return "", fmt.Errorf("node with ID %d not found", nodeVersionID)
		}
		return "", fmt.Errorf("failed to retrieve html_div for node %d: %w", nodeVersionID, err)
	}
	return htmlDiv, nil
}

// GetLatestHTMLEdge retrieves the html_div content of the latest version of an edge.
func (g *GraphDB) GetLatestHTMLEdge(edgeVersionID int64) (string, error) {
	var htmlDiv string
	query := `SELECT html_div FROM edges WHERE edge_version_id = ?`
	err := g.db.QueryRow(query, edgeVersionID).Scan(&htmlDiv)
	if err != nil {
		return "", fmt.Errorf("failed to retrieve html_div for edge %d: %w", edgeVersionID, err)
	}
	return htmlDiv, nil
}

// ListAvailableNodes retrieves all nodes and displays their version_id and name.
func (g *GraphDB) ListAvailableNodes() ([]struct {
	ID   int64
	Name string
}, error) {
	query := `SELECT node_version_id, node_name FROM nodes`
	rows, err := g.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to retrieve available nodes: %w", err)
	}
	defer rows.Close()

	var nodes []struct {
		ID   int64
		Name string
	}

	for rows.Next() {
		var id int64
		var name string
		if err := rows.Scan(&id, &name); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}
		nodes = append(nodes, struct {
			ID   int64
			Name string
		}{id, name})
	}

	return nodes, nil
}

// RootNodeExists checks if a root node (original_node_version_id = 0) exists.
func (g *GraphDB) RootNodeExists() (bool, error) {
	var count int
	query := `SELECT COUNT(*) FROM nodes WHERE original_node_version_id = 0`
	err := g.db.QueryRow(query).Scan(&count)
	if err != nil {
		return false, fmt.Errorf("failed to check for root node: %w", err)
	}

	return count > 0, nil
}

func (g *GraphDB) CreateNode(nodeName string, connectedNodeID int64, htmlDiv string, authorEmail string) (int64, error) {
	insertNodeQuery := `INSERT INTO nodes (node_name, html_div, author_email) VALUES (?, ?, ?)`
	_, err := g.db.Exec(insertNodeQuery, nodeName, htmlDiv, authorEmail)
	if err != nil {
		return 0, fmt.Errorf("failed to create node: %w", err)
	}

	newNodeID, err := g.GetLastInsertedNodeVersionID()
	if err != nil {
		return 0, err
	}

	updateQuery := `UPDATE nodes SET original_node_version_id = ? WHERE node_version_id = ?`
	_, err = g.db.Exec(updateQuery, newNodeID, newNodeID)
	if err != nil {
		return 0, fmt.Errorf("failed to update original_node_version_id: %w", err)
	}

	// Enforce edge creation
	if connectedNodeID != 0 {
		err = g.CreateEdge(connectedNodeID, newNodeID, htmlDiv, authorEmail)
		if err != nil {
			return 0, fmt.Errorf("failed to connect nodes: %w", err)
		}
	} else {
		// If no connected node ID is provided, connect to the root node (0)
		err = g.CreateEdge(0, newNodeID, htmlDiv, authorEmail)
		if err != nil {
			return 0, fmt.Errorf("failed to connect node to root: %w", err)
		}
	}

	return newNodeID, nil
}

func (g *GraphDB) CreateEdge(fromNodeID, toNodeID int64, htmlDiv string, authorEmail string) error {
	connectNodesQuery := `INSERT INTO edges (edge_name, from_node_version_id, to_node_version_id, html_div, author_email) VALUES (?, ?, ?, ?, ?)`
	_, err := g.db.Exec(connectNodesQuery, "edge_between_nodes", fromNodeID, toNodeID, htmlDiv, authorEmail)
	if err != nil {
		return fmt.Errorf("failed to create edge between node %d and node %d: %w", fromNodeID, toNodeID, err)
	}
	return nil
}

// CheckRootNodeByID checks if a root node exists by checking for ID = 1.
func (g *GraphDB) CheckRootNodeByID(nodeID int64) (bool, error) {
	var count int
	query := `SELECT COUNT(*) FROM nodes WHERE node_version_id = ?`
	err := g.db.QueryRow(query, nodeID).Scan(&count)
	if err != nil {
		return false, fmt.Errorf("failed to check for root node with ID %d: %w", nodeID, err)
	}

	return count > 0, nil
}

// ListAvailableEdges retrieves all edges and returns them with from and to node IDs.
func (g *GraphDB) ListAvailableEdges() ([]struct {
	FromNode int64
	ToNode   int64
}, error) {
	query := `SELECT from_node_version_id, to_node_version_id FROM edges`
	rows, err := g.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to retrieve available edges: %w", err)
	}
	defer rows.Close()

	var edges []struct {
		FromNode int64
		ToNode   int64
	}

	for rows.Next() {
		var fromNode, toNode int64
		if err := rows.Scan(&fromNode, &toNode); err != nil {
			return nil, fmt.Errorf("failed to scan row: %w", err)
		}
		edges = append(edges, struct {
			FromNode int64
			ToNode   int64
		}{fromNode, toNode})
	}

	return edges, nil
}

// ..\Documents\problem-graph\handlers\http.go
package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"

	"problem-graph/database"
)

// NodeRequest defines the structure for a node request
type NodeRequest struct {
	NodeName      string `json:"node_name"`
	ConnectedNode int64  `json:"connected_node"`
	HTMLContent   string `json:"html_content"`
	AuthorEmail   string `json:"author_email"`
}

// CreateNodeHTTP handles creating or revising a node via HTTP
func CreateNodeHTTP(w http.ResponseWriter, r *http.Request, graphDB *database.GraphDB) {
	nodeName := r.FormValue("node_name")
	description := r.FormValue("description")
	imageUrl := r.FormValue("image_url")
	imageLink := r.FormValue("image_link")

	// Build the HTML content for the node
	nodeHTML := fmt.Sprintf("<h2>%s</h2><p>%s</p>", nodeName, description)
	if imageUrl != "" {
		if imageLink != "" {
			nodeHTML += fmt.Sprintf(`<a href="%s" target="_blank"><img src="%s" alt="Node Image" style="max-width: 300px;"></a>`, imageLink, imageUrl)
		} else {
			nodeHTML += fmt.Sprintf(`<img src="%s" alt="Node Image" style="max-width: 300px;">`, imageUrl)
		}
	}

	connectedNodeIDStr := r.FormValue("connected_node")
	connectedNodeID, err := strconv.ParseInt(connectedNodeIDStr, 10, 64)
	if err != nil {
		http.Error(w, "Invalid connected node ID", http.StatusBadRequest)
		return
	}

	// Save the node to the database using the graphDB
	_, err = graphDB.CreateNode(nodeName, connectedNodeID, nodeHTML, r.FormValue("author_email"))
	if err != nil {
		http.Error(w, "Failed to create node", http.StatusInternalServerError)
		return
	}

	// Respond with the newly created node's HTML so it can be appended to the DOM
	w.Write([]byte(nodeHTML))
}

// RetrieveNodeHTTP handles fetching node information by node ID via HTTP
func RetrieveNodeHTTP(w http.ResponseWriter, r *http.Request, graphDB *database.GraphDB) {
	nodeIDStr := r.URL.Query().Get("node_id")
	nodeID, err := strconv.ParseInt(nodeIDStr, 10, 64)
	if err != nil {
		http.Error(w, "Invalid node ID", http.StatusBadRequest)
		return
	}

	htmlDiv, err := graphDB.GetLatestHTMLNode(nodeID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	json.NewEncoder(w).Encode(map[string]string{"html_div": htmlDiv})
}

// ServeNodesHTML serves the list of nodes in a simple HTML format
func ServeNodesHTML(w http.ResponseWriter, graphDB *database.GraphDB) {
	// Fetch the list of available nodes and their edges
	nodes, err := graphDB.ListAvailableNodes()
	if err != nil {
		http.Error(w, "Failed to fetch nodes", http.StatusInternalServerError)
		return
	}

	edges, err := graphDB.ListAvailableEdges() // Fetch available edges
	if err != nil {
		http.Error(w, "Failed to fetch edges", http.StatusInternalServerError)
		return
	}

	// Begin the HTML response
	w.Header().Set("Content-Type", "text/html")
	fmt.Fprintf(w, "<html><head><title>Node Graph</title><style>")
	fmt.Fprintf(w, "details { margin-left: 20px; }") // CSS for indentation of nested nodes
	fmt.Fprintf(w, "</style><script src='https://unpkg.com/htmx.org'></script></head><body>")
	fmt.Fprintf(w, "<h1>Node Graph</h1>")

	// Start of static HTML generation for nodes
	if len(nodes) == 0 {
		fmt.Fprintf(w, "<p>No nodes available yet.</p>")
	} else {
		// Map to hold edges between nodes
		nodeMap := make(map[int64][]int64)
		for _, edge := range edges {
			nodeMap[edge.FromNode] = append(nodeMap[edge.FromNode], edge.ToNode)
		}

		// Find the root nodes (nodes that are not children)
		rootNodes := findRootNodes(nodes, nodeMap)

		// Render root nodes and their child nodes
		fmt.Fprintf(w, `<div id="node-list">`)
		for _, rootNode := range rootNodes {
			renderNodeStatic(w, nodes, nodeMap, rootNode.ID)
		}
		fmt.Fprintf(w, `</div>`)
	}
}

// findRootNodes identifies the nodes that are not children of any other node.
func findRootNodes(nodes []struct {
	ID   int64
	Name string
}, nodeMap map[int64][]int64) []struct {
	ID   int64
	Name string
} {
	childNodeSet := make(map[int64]bool)
	for _, childNodes := range nodeMap {
		for _, childID := range childNodes {
			childNodeSet[childID] = true
		}
	}

	var rootNodes []struct {
		ID   int64
		Name string
	}
	for _, node := range nodes {
		if !childNodeSet[node.ID] {
			rootNodes = append(rootNodes, node)
		}
	}
	return rootNodes
}

// Helper function to recursively render nodes in a top-down fashion (root first)
func renderNodeStatic(w http.ResponseWriter, nodes []struct {
	ID   int64
	Name string
}, nodeMap map[int64][]int64, parentID int64) {
	// Print the parent node first
	for _, node := range nodes {
		if node.ID == parentID {
			fmt.Fprintf(w, `<details class="node" data-node-id="%d"><summary>%s (ID: %d)</summary>`, node.ID, node.Name, node.ID)

			// Recursively render child nodes in a top-down manner (root-first)
			if childIDs, exists := nodeMap[node.ID]; exists {
				for _, childID := range childIDs {
					renderNodeStatic(w, nodes, nodeMap, childID)
				}
			}
			fmt.Fprintf(w, "</details>")
		}
	}
}

// ..\Documents\problem-graph\main.go
package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"runtime"
	"sync"
	"syscall"

	"problem-graph/database"
	"problem-graph/handlers"
)

func StartHTTPServer(graphDB *database.GraphDB, wg *sync.WaitGroup) {
	defer wg.Done()

	http.HandleFunc("/create-node", func(w http.ResponseWriter, r *http.Request) {
		handlers.CreateNodeHTTP(w, r, graphDB)
	})

	// Load existing nodes on page load
	http.HandleFunc("/load-nodes", func(w http.ResponseWriter, r *http.Request) {
		handlers.ServeNodesHTML(w, graphDB)
	})

	// Serve static files
	http.Handle("/", http.FileServer(http.Dir("./static")))

	fmt.Println("Starting HTTP server on :8080...")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatalf("HTTP server error: %v", err)
	}
}

func LaunchBrowser(url string) {
	var cmd *exec.Cmd

	// Detect OS and configure browser command without address bar
	switch os := runtime.GOOS; os {
	case "windows":
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", url)
	case "darwin":
		cmd = exec.Command("open", "-na", "Google Chrome", "--args", "--app="+url)
	case "linux":
		cmd = exec.Command("google-chrome", "--app="+url)
	default:
		fmt.Printf("unsupported platform")
		return
	}

	if err := cmd.Start(); err != nil {
		log.Fatalf("Failed to launch browser: %v", err)
	}
}

func main() {
	dbFilePath := "sqlite_database.db"

	// Initialize the GraphDB
	graphDB, err := database.NewGraphDB(dbFilePath)
	if err != nil {
		log.Fatalf("Error initializing GraphDB: %v", err)
	}
	defer graphDB.Close()

	// Setup signal handling
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	var wg sync.WaitGroup
	wg.Add(1)

	go StartHTTPServer(graphDB, &wg)

	// Launch the browser after the server starts
	LaunchBrowser("http://localhost:8080")

	<-sigs
	fmt.Println("\nReceived shutdown signal. Shutting down gracefully...")

	wg.Wait()
	fmt.Println("All operations completed successfully.")
}

// ..\Documents\problem-graph\database\database.go
package database

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"sync"

	_ "modernc.org/sqlite" // SQLite driver
)

// GraphDB represents the database connection and schema setup.
// It also includes a mutex for concurrency control.
type GraphDB struct {
	db *sql.DB
	mu *sync.Mutex // Make it a pointer to share across functions
}

// SQLite SQL commands to create the necessary sequences and tables
var sqliteSchema = []string{
	// Create 'nodes' table with an html_div and author_email column
	`CREATE TABLE IF NOT EXISTS nodes (
		node_version_id INTEGER PRIMARY KEY AUTOINCREMENT,
		node_name TEXT,
		original_node_version_id INTEGER,
		node_timestamp_gmt DATETIME DEFAULT CURRENT_TIMESTAMP,
		html_div TEXT,  -- Column to store HTML content
		author_email TEXT  -- Column to store the email of the person creating or revising the node
	);`,

	`INSERT INTO nodes (node_version_id, node_name, original_node_version_id, html_div, author_email)
	 SELECT 0, 'Root', 0, '<p>Root Node</p>', 'default_root@example.com'
	 WHERE NOT EXISTS (SELECT 1 FROM nodes WHERE node_version_id = 0);`,

	// Create 'edges' table with an html_div column
	`CREATE TABLE IF NOT EXISTS edges (
		edge_version_id INTEGER PRIMARY KEY AUTOINCREMENT,
		edge_name TEXT,
		from_node_version_id INTEGER,
		to_node_version_id INTEGER,
		edge_timestamp_gmt DATETIME DEFAULT CURRENT_TIMESTAMP,
		html_div TEXT,  -- Column to store HTML content
        author_email TEXT
	);`,
}

// ensureDirectoryExists ensures that the directory for the database file exists and returns an error if it doesn't.
func ensureDirectoryExists(dbPath string) error {
	dir := filepath.Dir(dbPath)
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		return fmt.Errorf("directory %s does not exist", dir)
	}
	return nil
}

// NewGraphDB initializes a connection to SQLite and returns a GraphDB instance.
// It also creates the necessary sequences and tables.
func NewGraphDB(dbFilePath string) (*GraphDB, error) {
	// Ensure the directory exists (return an error if not)
	err := ensureDirectoryExists(dbFilePath)
	if err != nil {
		return nil, err
	}

	// Open SQLite database (will create the file if it doesn't exist)
	db, err := sql.Open("sqlite", dbFilePath)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to SQLite: %w", err)
	}

	// Initialize the GraphDB struct with a shared mutex
	graphDB := &GraphDB{db: db, mu: &sync.Mutex{}}

	// Create sequences and tables
	err = graphDB.createSchema()
	if err != nil {
		return nil, fmt.Errorf("failed to create schema: %w", err)
	}

	return graphDB, nil
}

// createSchema ensures that the necessary sequences and tables are created.
func (g *GraphDB) createSchema() error {
	for _, stmt := range sqliteSchema {
		_, err := g.db.Exec(stmt)
		if err != nil {
			return fmt.Errorf("failed to execute statement: %w\nStatement: %s", err, stmt)
		}
	}
	return nil
}

// Close closes the database connection.
func (g *GraphDB) Close() error {
	return g.db.Close()
}


Show only the FUNCTIONS that need to be changed. do not include functions that do not require changes
show the ENTIRE BODY of any modified FUNCTIONS before and after in SEPERATE code blocks

IF ANY CHANGES TO IMPORTS, put these in a sperate code block
