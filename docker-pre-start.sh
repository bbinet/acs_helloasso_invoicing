#!/bin/bash

# Import our environment variables from systemd
while IFS= read -rd '' var; do export "$var"; done </proc/1/environ

abort() {
    msg="$1"
    echo "$msg"
    echo "=> Environment was:"
    env
    echo "=> Program terminated!"
    exit 1
}

create_user() {
    user=$1
    password=$2
    if [ -z "${user}" ] || [ -z "${password}" ]; then
        abort "=> create_user 2 args are required (user, password)."
    fi
    useradd --create-home --shell /bin/bash ${user}
    chmod 700 /home/${user}
    mkdir -p -m 700 /home/${user}/.ssh
    chown -R ${user}:${user} /home/${user}
    echo "${user}:${password}" | chpasswd
    if [ $? -eq 0 ]; then
        echo "=> User \"${user}\" ok."
    else
        abort "=> Failed to create user \"${user}\"!"
    fi
}

# create users from environment variables and docker secrets
if [ -z "${PRE_CREATE_USERS}" ]; then
    echo "=> No user names supplied: no user will be created."
else
    for user in $(echo ${PRE_CREATE_USERS} | tr "," "\n"); do
        if [ -f "/run/secrets/${user}.password" ]
        then
            create_user $user $(cat "/run/secrets/${user}.password")
        else
            userpassword_var="${user}_PASSWORD"
            create_user $user ${!userpassword_var}
        fi
    done
fi
