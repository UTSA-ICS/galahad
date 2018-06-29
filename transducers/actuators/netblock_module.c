//*************************************************************
//      Netfilter Module for blocking network access          *
//							      *
//	Copyright (c) 2018 by Raytheon BBN Technologies Corp. *
//							      *
//*************************************************************



#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/fs.h>
#include "kmap.h"

MODULE_AUTHOR("Raytheon BBN Technologies");
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Network and Transport Layer Firewall");
MODULE_VERSION("0.1");


//   Variables pertaining to character device driver
//   Character Device driver used as user to kernel commununication
//   mechanism
static int majorNumber;
static char message[256] = {0};
static short size_of_message;
static int numberOpens = 0;
static struct class*  netblockcharClass  = NULL;
static struct device* netblockcharDevice = NULL;

//   Prototype functions for character device driver
static int device_open(struct inode *, struct file *);
static int device_release(struct inode *, struct file *);
static ssize_t device_write(struct file *, const char *, size_t, loff_t *);


//   File Operations structure for character device callbacks
static struct file_operations fops = {
	.write = device_write,
	.open = device_open,
	.release = device_release,
};

//   Character Device
#define  DEVICE_NAME "netblockchar"
#define  CLASS_NAME  "netblock"



//   netfilter hook options
static struct nf_hook_ops nfho_in;
static struct nf_hook_ops nfho_out;

struct packetRules {
	//Struct for holding different types of rules
	map_int_t in_ports;
	map_int_t out_ports;
	map_int_t in_ip;
	map_int_t out_ip;
};

//   Structure for holding all the firewall rules
static struct packetRules rules;

//   Incoming packets hook
unsigned int port_blocker_in_hook(void* priv, struct sk_buff *skb, const struct nf_hook_state *state){

	struct iphdr* ip_header;
	struct tcphdr* tcp_header;
	uint16_t dst_port;
	uint16_t src_port;
	char dport[6];
	char ip_src[16];
	char ip_dst[16];
	int* val;

	if(!skb){
		return NF_ACCEPT;
	}


	ip_header = ip_hdr(skb);
	if(!ip_header){
		return NF_ACCEPT;
	}

	//retrieve source and destination addresses for the packet
	//Convert Source IP Decimal into IPv4 string
	snprintf(ip_src, 16, "%pI4", &ip_header->saddr);

	//Convert Destination IP Decimal into IPv4 string
	snprintf(ip_dst, 16, "%pI4", &ip_header->daddr);

	val = map_get(&rules.in_ip, ip_src);
	if(val != NULL){
		//drop traffic
		*val = *val + 1;
		printk(KERN_INFO "Blocking traffic incoming from IP Address: %s\n", ip_src);
		return NF_DROP;
	}


	if (ip_header->protocol == IPPROTO_TCP){


		tcp_header = (struct tcphdr*)((__u32*)ip_header + ip_header->ihl);
		if(!tcp_header){
			return NF_ACCEPT;
		}

		dst_port = ntohs(tcp_header->dest);
		src_port = ntohs(tcp_header->source);
		snprintf(dport, 6, "%d", dst_port);
		val = map_get(&rules.in_ports, dport);

		if(val != NULL){
			printk(KERN_INFO "Blocking TCP traffic incoming to port: %d\n", dst_port);
			return NF_DROP;
		}

	}

	return NF_ACCEPT;
}


//   Outgoing packets hook
unsigned int port_blocker_out_hook(void* priv, struct sk_buff *skb, const struct nf_hook_state *state){

	struct iphdr* ip_header;
	struct tcphdr* tcp_header;
	uint16_t dst_port;
	uint16_t src_port;

	char ip_src[16];
	char ip_dst[16];
	char sport[6];
	int* val;

	if(!skb){
		return NF_ACCEPT;
	}


	ip_header = ip_hdr(skb);
	if(!ip_header){
		return NF_ACCEPT;
	}

	//retrieve source and destination addresses for the packet
	//Convert Source IP Decimal into IPv4 string
	snprintf(ip_src, 16, "%pI4", &ip_header->saddr);

	//Convert Destination IP Decimal into IPv4 string
	snprintf(ip_dst, 16, "%pI4", &ip_header->daddr);

	val = map_get(&rules.out_ip, ip_dst);
	if(val != NULL){
		printk(KERN_INFO "Blocking outgoing traffic to IP address: %s\n", ip_dst);
		return NF_DROP;
	}


	if (ip_header->protocol == IPPROTO_TCP){

		tcp_header = (struct tcphdr*)((__u32*)ip_header + ip_header->ihl);
		if(!tcp_header){
			return NF_ACCEPT;
		}

		dst_port = ntohs(tcp_header->dest);
		src_port = ntohs(tcp_header->source);
		snprintf(sport, 6, "%d", src_port);
		val = map_get(&rules.out_ports, sport);

		if(val != NULL){
			printk(KERN_INFO "Blocking outgoing TCP traffic originating from port: %d\n", src_port);
			return NF_DROP;
		}



	}

	return NF_ACCEPT;
}


//Called when the module is loaded
int init_module(){

	//Dynamically get Major number for character device driver
	majorNumber = register_chrdev(0, DEVICE_NAME, &fops);
	if (majorNumber<0){
		printk(KERN_ALERT "netblock: failed to register a major number\n");
	      	return majorNumber;
	}
	printk(KERN_INFO "netblock: registered correctly with major number %d\n", majorNumber);

	// Register the device class
	netblockcharClass = class_create(THIS_MODULE, CLASS_NAME);
	if(IS_ERR(netblockcharClass)){
	      	unregister_chrdev(majorNumber, DEVICE_NAME);
	      	printk(KERN_ALERT "netblock: failed to register device class\n");
	      	return PTR_ERR(netblockcharClass);
	}
	printk(KERN_INFO "netblock: device class registered correctly\n");

	// Register the device driver
	netblockcharDevice = device_create(netblockcharClass, NULL, MKDEV(majorNumber, 0), NULL, DEVICE_NAME);
	if (IS_ERR(netblockcharDevice)){
	      	class_destroy(netblockcharClass);
	      	unregister_chrdev(majorNumber, DEVICE_NAME);
	      	printk(KERN_ALERT "netblock: failed to create the device\n");
	      	return PTR_ERR(netblockcharDevice);
	}
   	printk(KERN_INFO "netblock: device class created correctly\n");

	printk(KERN_INFO "Loading netblock module");

	//Set up Netfilter hook
	nfho_in.hook = port_blocker_in_hook;
	nfho_in.hooknum = NF_INET_LOCAL_IN;
	nfho_in.pf = PF_INET;
	nfho_in.priority = NF_IP_PRI_FIRST;
	nf_register_net_hook(&init_net, &nfho_in);

	nfho_out.hook = port_blocker_out_hook;
	nfho_out.hooknum = NF_INET_LOCAL_OUT;
	nfho_out.pf = PF_INET;
	nfho_out.priority = NF_IP_PRI_FIRST;
	nf_register_net_hook(&init_net, &nfho_out);

	//initialize hashmaps
	map_init(&rules.in_ports);
	map_init(&rules.out_ports);
	map_init(&rules.in_ip);
	map_init(&rules.out_ip);

	return 0;
}


//Called when the module is removed/unloaded
void cleanup_module(){

	device_destroy(netblockcharClass, MKDEV(majorNumber, 0));
   	class_unregister(netblockcharClass);
   	class_destroy(netblockcharClass);
   	unregister_chrdev(majorNumber, DEVICE_NAME);
   	printk(KERN_INFO "netblock: unregistering netblock character device\n");

	map_deinit(&rules.in_ports);
	map_deinit(&rules.out_ports);
	map_deinit(&rules.in_ip);
	map_deinit(&rules.out_ip);
	nf_unregister_net_hook(&init_net, &nfho_in);
	nf_unregister_net_hook(&init_net, &nfho_out);
}

static int device_open(struct inode *inodep, struct file *filep){
	numberOpens++;
   	printk(KERN_INFO "netblock: character device has been opened %d times\n", numberOpens);
   	return 0;
}

static ssize_t device_write(struct file *filep, const char *buffer, size_t len, loff_t *offset){
	int* val;
   	sprintf(message, "%s", buffer);
   	size_of_message = strlen(message);

	map_set(&rules.in_ip, message, 0);
	val = map_get(&rules.in_ip, message);

	printk(KERN_INFO "Blocking IP address %s\n", message);
   	return len;
}

static int device_release(struct inode *inodep, struct file *filep){
   	printk(KERN_INFO "netblock: character device successfully closed\n");
   	return 0;
}
