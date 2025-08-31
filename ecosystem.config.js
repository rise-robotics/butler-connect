module.exports = {
    apps: [{
        name: 'butler-connect',
        script: 'src/main.py',
        interpreter: './venv/bin/python',
        cwd: '/home/rav/projects/butler-connect',
        instances: 1,
        autorestart: true,
        watch: ['src'],
        watch_delay: 1000,
        watch_options: {
            followSymlinks: false
        },
        ignore_watch: [
            "node_modules",
            "logs",
            "__pycache__",
            "*.pyc",
            ".git",
            ".vscode",
            "venv",
            "*.log"
        ],
        max_memory_restart: '1G',
        env: {
            NODE_ENV: 'production',
            PYTHONPATH: '/home/rav/projects/butler-connect/src',
            ROS_DOMAIN_ID: '0',
            RMW_IMPLEMENTATION: 'rmw_cyclonedx_cpp',
            AMENT_PREFIX_PATH: '/opt/ros/jazzy',
            CMAKE_PREFIX_PATH: '/opt/ros/jazzy',
            LD_LIBRARY_PATH: '/opt/ros/jazzy/lib',
            PATH: '/opt/ros/jazzy/bin:' + process.env.PATH,
            PYTHONPATH: '/opt/ros/jazzy/lib/python3.12/site-packages:/home/rav/projects/butler-connect/src'
        },
        log_file: './logs/butler-connect.log',
        out_file: './logs/butler-connect-out.log',
        error_file: './logs/butler-connect-error.log',
        time: true,
        merge_logs: true
    }]
};
