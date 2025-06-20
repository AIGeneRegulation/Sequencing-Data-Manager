# SeqManager Troubleshooting Guide

## Common Issues and Solutions

### 1. Template Not Found Error

**Error**: `jinja2.exceptions.TemplateNotFound: index.html`

**Cause**: Flask cannot locate the HTML templates.

**Solutions**:

1. **Check file structure** - Ensure this directory structure exists:
   ```
   /workspace/
   ├── code/
   │   └── app.py
   ├── templates/
   │   └── index.html
   └── static/
       ├── css/
       └── js/
   ```

2. **Verify template file exists**:
   ```bash
   ls -la templates/index.html
   ```

3. **Use the local development script**:
   ```bash
   python local_run.py
   ```

4. **Docker troubleshooting**:
   ```bash
   # Rebuild the Docker image
   docker build -t seqmanager .
   
   # Check container file structure
   docker run -it seqmanager ls -la /app/templates/
   ```

### 2. Missing Dependencies

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solutions**:

1. **Install dependencies locally**:
   ```bash
   pip install --user flask flask-cors
   ```

2. **Use Docker** (recommended):
   ```bash
   ./run.sh demo
   ```

3. **Use the local development script**:
   ```bash
   python local_run.py  # Auto-installs dependencies
   ```

### 3. Permission Denied Errors

**Error**: `PermissionError: [Errno 13] Permission denied`

**Solutions**:

1. **Use user installation**:
   ```bash
   pip install --user flask flask-cors
   ```

2. **Run with Docker** (recommended):
   ```bash
   ./run.sh run -d /path/to/your/data
   ```

3. **Set executable permissions**:
   ```bash
   chmod +x run.sh
   chmod +x local_run.py
   ```

### 4. Port Already in Use

**Error**: `OSError: [Errno 98] Address already in use`

**Solutions**:

1. **Use different port**:
   ```bash
   ./run.sh run -p 8080
   ```

2. **Stop existing containers**:
   ```bash
   docker stop seqmanager-app
   docker rm seqmanager-app
   ```

3. **Find and kill process**:
   ```bash
   lsof -i :5000
   kill -9 <PID>
   ```

### 5. Docker Build Issues

**Error**: Various Docker-related errors

**Solutions**:

1. **Clean Docker cache**:
   ```bash
   docker system prune -f
   docker build --no-cache -t seqmanager .
   ```

2. **Check Docker status**:
   ```bash
   docker --version
   docker info
   ```

3. **Use Docker Compose**:
   ```bash
   docker-compose up --build
   ```

## Quick Fixes

### Reset Everything
```bash
# Stop all containers
docker stop $(docker ps -aq) 2>/dev/null || true

# Clean up
./run.sh clean

# Fresh start
./run.sh demo
```

### Test System Components

1. **Test file classification**:
   ```bash
   python test_system.py
   ```

2. **Test Flask setup**:
   ```bash
   python test_flask_setup.py
   ```

3. **Test local development**:
   ```bash
   python local_run.py
   ```

## Alternative Running Methods

### Method 1: Local Development (No Docker)
```bash
python local_run.py
```
- Automatically installs dependencies
- Creates sample data
- Runs on http://localhost:5000

### Method 2: Quick Docker Demo
```bash
./run.sh demo
```
- Uses Docker with sample data
- Runs in background
- Access at http://localhost:5000

### Method 3: Production Docker
```bash
./run.sh run -d /path/to/your/sequencing/data -p 8080 -b
```
- Uses your real data
- Runs on custom port
- Background mode

### Method 4: Manual Docker
```bash
docker build -t seqmanager .
docker run -p 5000:5000 -v /path/to/data:/data seqmanager
```

## Debugging Steps

1. **Check file structure**:
   ```bash
   find . -name "*.html" -o -name "*.py" -o -name "*.css" | head -20
   ```

2. **Verify paths**:
   ```bash
   python test_flask_setup.py
   ```

3. **Test core functionality**:
   ```bash
   python test_system.py
   ```

4. **Check Docker logs**:
   ```bash
   docker logs seqmanager-app
   ```

## Getting Help

If none of these solutions work:

1. **Check the logs**:
   - Local: Check console output
   - Docker: `docker logs seqmanager-app`

2. **Verify your environment**:
   - Python version: `python --version`
   - Docker version: `docker --version`
   - Available disk space: `df -h`

3. **Try the simplest approach**:
   ```bash
   python local_run.py
   ```

4. **Report the issue** with:
   - Full error message
   - Your operating system
   - Python version
   - Docker version (if using Docker)
   - Steps that led to the error

## Performance Tips

- For large datasets (>100GB), ensure adequate disk space
- Use SSD storage for better scanning performance
- Increase Docker memory allocation for very large datasets
- Consider running on a server with more RAM for production use

## Security Notes

- Only mount necessary directories to Docker containers
- Review files before deletion - operations cannot be undone
- Keep backups of important data
- Use the confirmation dialogs in the web interface
