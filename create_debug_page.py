"""
Browser Console Debug Helper - Check for JavaScript errors
"""
import requests
import time

def create_debug_page():
    """Create a simple debug page to test admin panel functionality"""
    
    debug_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel Debug</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .test-result { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
        .info { background-color: #d1ecf1; color: #0c5460; }
        button { margin: 5px; padding: 10px; }
    </style>
</head>
<body>
    <h1>Admin Panel Debug</h1>
    <div id="results"></div>
    
    <button onclick="testLogin()">Test Login</button>
    <button onclick="testKPIs()">Test KPIs</button>
    <button onclick="testMonthly()">Test Monthly</button>
    <button onclick="openAdminPanel()">Open Admin Panel</button>
    
    <script>
        const API_BASE = 'http://localhost:8000';
        let authToken = null;
        
        function addResult(message, type = 'info') {
            const div = document.createElement('div');
            div.className = `test-result ${type}`;
            div.innerHTML = new Date().toLocaleTimeString() + ': ' + message;
            document.getElementById('results').appendChild(div);
            console.log(message);
        }
        
        async function testLogin() {
            try {
                addResult('Testing login...', 'info');
                
                const response = await fetch(`${API_BASE}/api/booking/admin/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        username: 'test_superadmin',
                        password: 'TestPass123!'
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    authToken = data.access_token;
                    addResult(`✅ Login successful! Token: ${authToken.substring(0, 50)}...`, 'success');
                    localStorage.setItem('adminToken', authToken);
                } else {
                    addResult(`❌ Login failed: ${response.status} ${response.statusText}`, 'error');
                }
            } catch (error) {
                addResult(`❌ Login error: ${error.message}`, 'error');
            }
        }
        
        async function testKPIs() {
            if (!authToken) {
                addResult('❌ No auth token - run login first', 'error');
                return;
            }
            
            try {
                addResult('Testing KPIs...', 'info');
                
                const response = await fetch(`${API_BASE}/api/booking/admin/kpis`, {
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
                
                if (response.ok) {
                    const kpis = await response.json();
                    addResult(`✅ KPIs: Total=${kpis.total}, Week=${kpis.week}, Month=${kpis.month}, Waitlist=${kpis.waitlist}`, 'success');
                } else {
                    addResult(`❌ KPIs failed: ${response.status} ${response.statusText}`, 'error');
                }
            } catch (error) {
                addResult(`❌ KPIs error: ${error.message}`, 'error');
            }
        }
        
        async function testMonthly() {
            if (!authToken) {
                addResult('❌ No auth token - run login first', 'error');
                return;
            }
            
            try {
                addResult('Testing monthly endpoints...', 'info');
                
                // Test June 2025
                const juneResponse = await fetch(`${API_BASE}/api/booking/admin/monthly?year=2025&month=6`, {
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
                
                if (juneResponse.ok) {
                    const juneData = await juneResponse.json();
                    addResult(`✅ June 2025: ${juneData.length} bookings`, 'success');
                } else {
                    addResult(`❌ June 2025 failed: ${juneResponse.status}`, 'error');
                }
                
                // Test July 2025
                const julyResponse = await fetch(`${API_BASE}/api/booking/admin/monthly?year=2025&month=7`, {
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
                
                if (julyResponse.ok) {
                    const julyData = await julyResponse.json();
                    addResult(`✅ July 2025: ${julyData.length} bookings`, 'success');
                } else {
                    addResult(`❌ July 2025 failed: ${julyResponse.status}`, 'error');
                }
                
            } catch (error) {
                addResult(`❌ Monthly error: ${error.message}`, 'error');
            }
        }
        
        function openAdminPanel() {
            if (!authToken) {
                addResult('❌ No auth token - run login first', 'error');
                return;
            }
            
            addResult('Opening admin panel in new tab...', 'info');
            window.open('http://localhost:5176/admin-login', '_blank');
        }
        
        // Auto-run login test on load
        window.onload = function() {
            addResult('Debug page loaded. Testing basic connectivity...', 'info');
            testLogin();
        };
        
        // Monitor console errors
        window.addEventListener('error', function(e) {
            addResult(`🚨 JavaScript Error: ${e.message} at ${e.filename}:${e.lineno}`, 'error');
        });
        
    </script>
</body>
</html>
"""
    
    with open('c:/Users/surya/my-hibachi-frontend/admin_debug.html', 'w', encoding='utf-8') as f:
        f.write(debug_html)
    
    print("✅ Created debug page: admin_debug.html")
    print("📂 Location: c:/Users/surya/my-hibachi-frontend/admin_debug.html")
    print("🌐 Open in browser: file:///c:/Users/surya/my-hibachi-frontend/admin_debug.html")

if __name__ == "__main__":
    create_debug_page()
