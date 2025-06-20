#!/bin/bash

# Sequencing Data Management System - Quick Start Script
# Usage: ./run.sh [command] [options]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default settings
DATA_PATH="${DATA_PATH:-./sample_data}"
PORT="${PORT:-5000}"
IMAGE_NAME="seqmanager"
CONTAINER_NAME="seqmanager-app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to display usage
show_usage() {
    cat << EOF
Sequencing Data Management System - Quick Start

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    build       Build the Docker image
    run         Run the application (builds if needed)
    stop        Stop the running container
    logs        Show application logs
    clean       Stop container and remove image
    demo        Create sample data and run demo
    help        Show this help message

Options:
    -p, --port PORT     Port to run on (default: 5000)
    -d, --data PATH     Data directory to mount (default: ./sample_data)
    -b, --background    Run in background (daemon mode)

Examples:
    $0 demo                           # Quick demo with sample data
    $0 run -p 8080 -d /path/to/data  # Run on port 8080 with custom data
    $0 build                         # Build Docker image
    $0 logs                          # View application logs

EOF
}

# Function to check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
}

# Function to build Docker image
build_image() {
    log_info "Building Docker image: $IMAGE_NAME"
    docker build -t "$IMAGE_NAME" .
    log_success "Docker image built successfully"
}

# Function to create sample data
create_sample_data() {
    log_info "Creating sample sequencing data in $DATA_PATH"
    
    mkdir -p "$DATA_PATH"/{raw,aligned,intermediate,results,duplicates}
    
    # Create sample FASTQ files
    cat > "$DATA_PATH/raw/sample1_R1.fastq" << 'EOF'
@SEQ_ID_1
ATCGATCGATCGATCGATCGATCGATCGATCG
+
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
@SEQ_ID_2
GCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTA
+
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
EOF

    cat > "$DATA_PATH/raw/sample1_R2.fastq" << 'EOF'
@SEQ_ID_1
CGATCGATCGATCGATCGATCGATCGATCGAT
+
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
@SEQ_ID_2
ATCGATCGATCGATCGATCGATCGATCGATCG
+
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
EOF

    # Compress FASTQ files
    gzip "$DATA_PATH/raw/sample1_R1.fastq" 2>/dev/null || true
    gzip "$DATA_PATH/raw/sample1_R2.fastq" 2>/dev/null || true
    
    # Create BAM file (mock)
    echo "Mock BAM file content" > "$DATA_PATH/aligned/sample1.sorted.bam"
    echo "Mock BAI file content" > "$DATA_PATH/aligned/sample1.sorted.bam.bai"
    
    # Create intermediate files
    echo "Alignment metrics data" > "$DATA_PATH/intermediate/sample1.metrics"
    echo "Processing log data" > "$DATA_PATH/intermediate/sample1.log"
    
    # Create results
    cat > "$DATA_PATH/results/sample1_final.vcf" << 'EOF'
##fileformat=VCFv4.2
##contig=<ID=chr1,length=249250621>
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chr1	100	.	A	T	60	PASS	.
chr1	200	.	G	C	80	PASS	.
EOF

    # Create duplicates
    cp "$DATA_PATH/results/sample1_final.vcf" "$DATA_PATH/duplicates/sample1_final_copy.vcf"
    
    log_success "Sample data created in $DATA_PATH"
}

# Function to run the application
run_app() {
    local background_mode=false
    local custom_port="$PORT"
    local custom_data="$DATA_PATH"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--port)
                custom_port="$2"
                shift 2
                ;;
            -d|--data)
                custom_data="$2"
                shift 2
                ;;
            -b|--background)
                background_mode=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    
    # Ensure data directory exists
    if [[ ! -d "$custom_data" ]]; then
        log_warning "Data directory $custom_data does not exist"
        read -p "Create sample data? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            DATA_PATH="$custom_data"
            create_sample_data
        fi
    fi
    
    # Check if image exists, build if not
    if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
        log_info "Docker image not found, building..."
        build_image
    fi
    
    # Stop existing container if running
    if docker container inspect "$CONTAINER_NAME" &> /dev/null; then
        log_info "Stopping existing container"
        docker stop "$CONTAINER_NAME" &> /dev/null || true
        docker rm "$CONTAINER_NAME" &> /dev/null || true
    fi
    
    # Run container
    local run_options=()
    if [[ "$background_mode" == true ]]; then
        run_options+=(-d)
        log_info "Starting container in background mode"
    else
        run_options+=(-it)
        log_info "Starting container in interactive mode"
    fi
    
    docker run \
        "${run_options[@]}" \
        --name "$CONTAINER_NAME" \
        -p "$custom_port:5000" \
        -v "$(realpath "$custom_data"):/data" \
        -v "$(pwd)/logs:/app/logs" \
        "$IMAGE_NAME"
    
    if [[ "$background_mode" == true ]]; then
        log_success "Application started in background"
        log_info "Access the web interface at: http://localhost:$custom_port"
        log_info "View logs with: $0 logs"
        log_info "Stop with: $0 stop"
    fi
}

# Function to stop the application
stop_app() {
    if docker container inspect "$CONTAINER_NAME" &> /dev/null; then
        log_info "Stopping $CONTAINER_NAME"
        docker stop "$CONTAINER_NAME"
        docker rm "$CONTAINER_NAME"
        log_success "Application stopped"
    else
        log_warning "Container $CONTAINER_NAME is not running"
    fi
}

# Function to show logs
show_logs() {
    if docker container inspect "$CONTAINER_NAME" &> /dev/null; then
        docker logs -f "$CONTAINER_NAME"
    else
        log_error "Container $CONTAINER_NAME is not running"
        exit 1
    fi
}

# Function to clean up
clean_up() {
    stop_app
    if docker image inspect "$IMAGE_NAME" &> /dev/null; then
        log_info "Removing Docker image"
        docker rmi "$IMAGE_NAME"
        log_success "Cleanup completed"
    fi
}

# Function to run demo
run_demo() {
    log_info "Setting up demo environment"
    DATA_PATH="./sample_data"
    create_sample_data
    run_app -b
    
    echo
    log_success "Demo is ready!"
    echo
    echo "🧬 Sequencing Data Management System Demo"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🌐 Web Interface: http://localhost:$PORT"
    echo "📁 Sample Data: $DATA_PATH"
    echo "📋 View Logs: $0 logs"
    echo "🛑 Stop Demo: $0 stop"
    echo
}

# Main script logic
case "${1:-help}" in
    build)
        check_docker
        build_image
        ;;
    run)
        check_docker
        shift
        run_app "$@"
        ;;
    stop)
        check_docker
        stop_app
        ;;
    logs)
        check_docker
        show_logs
        ;;
    clean)
        check_docker
        clean_up
        ;;
    demo)
        check_docker
        run_demo
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
