sudo yum -y update
sudo yum -y install https://centos7.iuscommunity.org/ius-release.rpm
sudo yum -y install git python36u python36u-pip python36u-devel
sudo yum -y groupinstall development
sudo pip3.6 install netifaces psutil
git clone https://github.com/hdb3/BGPspeaker.git
cd BGPspeaker/
sudo python3.6 ./helloworld.py
