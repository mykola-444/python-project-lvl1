#!/bin/bash -ex

if [[ -z "$DOCKER_IMAGE" ]]; then
    echo "DOCKER_IMAGE is not defined"
    exit 1
fi

# install software
yum update -y
yum install -y awscli java-1.8.0 docker htop python3 iotop git
yum remove -y java-1.7.0
yum clean all

# add ec2-user to docker group
usermod -aG docker ec2-user
service docker start

# pull docker image
docker pull $DOCKER_IMAGE

# create admin user and add it to docker group:
groupadd -g 1002 bldadmin && \
useradd -c 'Unprivileged Jenkins user' -g bldadmin -m -s /bin/bash -u 1002 -d /home/bldadmin bldadmin
usermod -aG docker bldadmin

# create directory with ssh keys
mkdir /home/bldadmin/.ssh
chmod 700 /home/bldadmin/.ssh

cat > /home/bldadmin/.ssh/authorized_keys << EOF
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC4XXefabE4GR4u+DpL/5uo6pdHRi7LHo/4y/Xxd0QoPgSVF2vl9vYqL4Dre39cQv2eMRFhSu7egyMRxovH3NizYXi7vIcmXSSVY111fdBGveDBgmYAqp9TEe/BwCCwqwINsboQ7ggAmpB7N/uVhwBn/s0XRBQp5QTslNkrC3G2M0qQwnH9SWKT5vaZWaN45PKKDZeCSIWm5l0eO0Ihz/a4UntyQ4eN9cE4P30N596eOIQAtv0HzCXgR/RwvGXtbPGV1HQKuph/2faUbn8DtYbCiW98RzTGwcOOahnSqP9W2pFeoze1seqFrr3GnS7MjkQUwUw/WrrmPkfoGvDSzMFz7Viwinud/qVBs0j0KpYf07eLo9dZB+4T+Evmh8dmmu97ISNRf1p31nMEw1qSpJeWUEoEZWZnxWx8dPpjVHzSoRBSxCAvMpGGn59h4pfN26nfu+2bfp8WGAAUEBxp2+CkCDEGHZlBkcxxksjblovgLR6QHss7tGTkUSFsiugN1LhSWMFmq8oHE0NhPWMsAsyFLfK2GiQ6y5/wdUdEYJNFo7aaHr/lCGncb38NqflUuuyoHDdk9GrGVhVB4ojqdh1k8Wl8HwUcrQFXuknd0EBbUs+6jN2iESl+r5mgxf/1sa7V2dKCfKMI2/X9l9j+AJPiAew8tVLXc0lH7sPSWEud7Q==
EOF
chmod 600 /home/bldadmin/.ssh/authorized_keys
chown -R bldadmin:bldadmin /home/bldadmin/.ssh

# Create directory for local cache
mkdir /home/bldadmin/data
chown -R bldadmin:bldadmin /home/bldadmin/data

