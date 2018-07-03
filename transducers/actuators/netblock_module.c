/*
*****************************************************************
      Netfilter Module for blocking network access              *
							        *
      Copyright (c) 2018 by Raytheon BBN Technologies Corp.     *
							        *
*****************************************************************
*/

#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/netfilter_ipv6.h>
#include <linux/ip.h>
#include <linux/ipv6.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/fs.h>
#include <linux/string.h>
#include "include/kmap.h"

MODULE_AUTHOR("Raytheon BBN Technologies");
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Network and Transport Layer Firewall");
MODULE_VERSION("0.1");


//   Rule operations
#define UNBLOCK_OUTGOING_IPV4_IP 0
#define BLOCK_OUTGOING_IPV4_IP 1
#define UNBLOCK_INCOMING_IPV4_IP 2
#define BLOCK_INCOMING_IPV4_IP 3
#define UNBLOCK_OUTGOING_IPV6_IP 4
#define BLOCK_OUTGOING_IPV6_IP 5
#define UNBLOCK_INCOMING_IPV6_IP 6
#define BLOCK_INCOMING_IPV6_IP 7
#define UNBLOCK_OUTGOING_TCP_PORT 8
#define BLOCK_OUTGOING_TCP_PORT 9
#define UNBLOCK_INCOMING_TCP_PORT 10
#define BLOCK_INCOMING_TCP_PORT 11
#define UNBLOCK_OUTGOING_UDP_PORT 12
#define BLOCK_OUTGOING_UDP_PORT 13
#define UNBLOCK_INCOMING_UDP_PORT 14
#define BLOCK_INCOMING_UDP_PORT 15


//   Commands
#define BLOCK "block"
#define UNBLOCK "unblock"
#define INCOMING "incoming"
#define OUTGOING "outgoing"
#define IPV4 "ipv4"
#define IPV6 "ipv6"
#define TCP "tcp"
#define UDP "udp"

//   Character Device
#define  DEVICE_NAME "netblockchar"
#define  CLASS_NAME  "netblock"


//   Variables pertaining to character device driver
//   Character Device driver used as user to kernel commununication
//   mechanism
static int majorNumber;
static char message[256] = {0};
static struct class*  netblockcharClass  = NULL;
static struct device* netblockcharDevice = NULL;

//   Prototype functions for character device driver
static int device_open(struct inode *, struct file *);
static int device_release(struct inode *, struct file *);
static ssize_t device_write(struct file *, const char *, size_t, loff_t *);
static ssize_t device_read(struct file *, char *, size_t, loff_t *);

//   File Operations structure for character device driver callbacks
static struct file_operations fops = {
	.write = device_write,
	.open = device_open,
	.release = device_release,
	.read = device_read,
};


//   netfilter hook options
static struct nf_hook_ops nfho_ipv4_in;
static struct nf_hook_ops nfho_ipv4_out;
static struct nf_hook_ops nfho_ipv6_in;
static struct nf_hook_ops nfho_ipv6_out;


struct packetRules {
	//Hashmaps for various types of firewall rules
	map_int_t in_tcp_ports;
	map_int_t out_tcp_ports;
	map_int_t in_udp_ports;
	map_int_t out_udp_ports;
	map_int_t in_ipv4;
	map_int_t out_ipv4;
	map_int_t in_ipv6;
	map_int_t out_ipv6;
};

//   Structure for holding all the firewall rules
static struct packetRules rules;

//   Incoming IPv4 packets hook
unsigned int ipv4_in_hook(void* priv, struct sk_buff *skb, const struct nf_hook_state *state){

	struct iphdr* ip_header;
	struct tcphdr* tcp_header;
	struct udphdr* udp_header;
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

	val = map_get(&rules.in_ipv4, ip_src);
	if(val != NULL){
		//drop traffic
		*val = *val + 1;
		printk(KERN_INFO "netblock: blocking traffic incoming from IP Address: %s\n", ip_src);
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
		val = map_get(&rules.in_tcp_ports, dport);

		if(val != NULL){
			printk(KERN_INFO "netblock: blocking TCP traffic incoming to port: %d\n", dst_port);
			return NF_DROP;
		}

	}else if (ip_header->protocol == IPPROTO_UDP){


		udp_header = (struct udphdr*)((__u32*)ip_header + ip_header->ihl);
		if(!udp_header){
			return NF_ACCEPT;
		}

		dst_port = ntohs(udp_header->dest);
		src_port = ntohs(udp_header->source);
		snprintf(dport, 6, "%d", dst_port);
		val = map_get(&rules.in_udp_ports, dport);

		if(val != NULL){
			printk(KERN_INFO "netblock: blocking UDP traffic incoming to port: %d\n", dst_port);
			return NF_DROP;
		}

	}

	return NF_ACCEPT;
}


//   Outgoing IPv4 packets hook
unsigned int ipv4_out_hook(void* priv, struct sk_buff *skb, const struct nf_hook_state *state){

	struct iphdr* ip_header;
	struct tcphdr* tcp_header;
	struct udphdr* udp_header;
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


	val = map_get(&rules.out_ipv4, ip_dst);
	if(val != NULL){
		printk(KERN_INFO "netblock: blocking outgoing traffic to IP address: %s\n", ip_dst);
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
		val = map_get(&rules.out_tcp_ports, sport);

		if(val != NULL){
			printk(KERN_INFO "netblock: blocking outgoing TCP traffic originating from port: %d\n", src_port);
			return NF_DROP;
		}



	}else if (ip_header->protocol == IPPROTO_UDP){

		udp_header = (struct udphdr*)((__u32*)ip_header + ip_header->ihl);
		if(!udp_header){
			return NF_ACCEPT;
		}

		dst_port = ntohs(udp_header->dest);
		src_port = ntohs(udp_header->source);
		snprintf(sport, 6, "%d", src_port);
		val = map_get(&rules.out_udp_ports, sport);

		if(val != NULL){
			printk(KERN_INFO "netblock: blocking outgoing UDP traffic originating from port: %d\n", src_port);
			return NF_DROP;
		}

	}

	return NF_ACCEPT;
}

//   Incoming IPv6 packets hook
unsigned int ipv6_in_hook(void* priv, struct sk_buff *skb, const struct nf_hook_state *state){

	struct ipv6hdr* ip_header;
	struct tcphdr* tcp_header;
	struct udphdr* udp_header;
	uint16_t dst_port;
	uint16_t src_port;
	char dport[6];
	char ip_src[40];
	char ip_dst[40];
	int* val;


	if(!skb){
		return NF_ACCEPT;
	}


	ip_header = ipv6_hdr(skb);
	if(!ip_header){
		return NF_ACCEPT;
	}


	//retrieve source and destination addresses for the packet
	//Convert Source IP Decimal into IPv6 string
	snprintf(ip_src, 40, "%pI6", &ip_header->saddr);

	//Convert Destination IP Decimal into IPv6 string
	snprintf(ip_dst, 40, "%pI6", &ip_header->daddr);

	printk(KERN_INFO "netblock: incoming IPv6 traffic from %s\n", ip_src);

	val = map_get(&rules.in_ipv6, ip_src);
	if(val != NULL){
		//drop traffic
		*val = *val + 1;
		printk(KERN_INFO "netblock: blocking traffic incoming from IPv6 Address: %s\n", ip_src);
		return NF_DROP;
	}

	if (ip_header->nexthdr == IPPROTO_TCP){


		tcp_header = (struct tcphdr*)ipipv6_hdr;
		if(!tcp_header){
			return NF_ACCEPT;
		}

		dst_port = ntohs(tcp_header->dest);
		src_port = ntohs(tcp_header->source);
		snprintf(dport, 6, "%d", dst_port);
		val = map_get(&rules.in_tcp_ports, dport);

		if(val != NULL){
			printk(KERN_INFO "netblock: blocking TCP traffic incoming to port: %d\n", dst_port);
			return NF_DROP;
		}

	}else if (ip_header->nexthdr == IPPROTO_UDP){


		udp_header = (struct udphdr*)ipipv6_hdr;
		if(!udp_header){
			return NF_ACCEPT;
		}

		dst_port = ntohs(udp_header->dest);
		src_port = ntohs(udp_header->source);
		snprintf(dport, 6, "%d", dst_port);
		val = map_get(&rules.in_udp_ports, dport);

		if(val != NULL){
			printk(KERN_INFO "netblock: blocking UDP traffic incoming to port: %d\n", dst_port);
			return NF_DROP;
		}

	}

	return NF_ACCEPT;
}

//   Outgoing IPv6 packets hook
unsigned int ipv6_out_hook(void* priv, struct sk_buff *skb, const struct nf_hook_state *state){

	struct ipv6hdr* ip_header;
	struct tcphdr* tcp_header;
	struct udphdr* udp_header;
	uint16_t dst_port;
	uint16_t src_port;

	char ip_src[40];
	char ip_dst[40];
	char sport[6];
	int* val;


	if(!skb){
		return NF_ACCEPT;
	}


	ip_header = ipv6_hdr(skb);
	if(!ip_header){
		return NF_ACCEPT;
	}

	//retrieve source and destination addresses for the packet
	//Convert Source IP Decimal into IPv4 string
	snprintf(ip_src, 40, "%pI6", &ip_header->saddr);

	//Convert Destination IP Decimal into IPv4 string
	snprintf(ip_dst, 40, "%pI6", &ip_header->daddr);

	val = map_get(&rules.out_ipv6, ip_dst);
	if(val != NULL){
		printk(KERN_INFO "netblock: blocking outgoing traffic to IPv6 address: %s\n", ip_dst);
		return NF_DROP;
	}


	if (ip_header->nexthdr == IPPROTO_TCP){

		tcp_header = (struct tcphdr*) ipipv6_hdr;
		if(!tcp_header){
			return NF_ACCEPT;
		}

		dst_port = ntohs(tcp_header->dest);
		src_port = ntohs(tcp_header->source);
		snprintf(sport, 6, "%d", src_port);
		val = map_get(&rules.out_tcp_ports, sport);

		if(val != NULL){
			printk(KERN_INFO "netblock: blocking outgoing TCP traffic originating from port: %d\n", src_port);
			return NF_DROP;
		}



	}else if (ip_header->nexthdr == IPPROTO_UDP){

		udp_header = (struct udphdr*)ipipv6_hdr;
		if(!udp_header){
			return NF_ACCEPT;
		}

		dst_port = ntohs(udp_header->dest);
		src_port = ntohs(udp_header->source);
		snprintf(sport, 6, "%d", src_port);
		val = map_get(&rules.out_udp_ports, sport);

		if(val != NULL){
			printk(KERN_INFO "netblock: blocking outgoing UDP traffic originating from port: %d\n", src_port);
			return NF_DROP;
		}

	}


	return NF_ACCEPT;
}



//   Called when the module is loaded
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
	nfho_ipv4_in.hook = ipv4_in_hook;
	nfho_ipv4_in.hooknum = NF_INET_LOCAL_IN;
	nfho_ipv4_in.pf = PF_INET;
	nfho_ipv4_in.priority = NF_IP_PRI_FIRST;
	nf_register_net_hook(&init_net, &nfho_ipv4_in);

	nfho_ipv4_out.hook = ipv4_out_hook;
	nfho_ipv4_out.hooknum = NF_INET_LOCAL_OUT;
	nfho_ipv4_out.pf = PF_INET;
	nfho_ipv4_out.priority = NF_IP_PRI_FIRST;
	nf_register_net_hook(&init_net, &nfho_ipv4_out);

	nfho_ipv6_in.hook = ipv6_in_hook;
	nfho_ipv6_in.hooknum = NF_INET_LOCAL_IN;
	nfho_ipv6_in.pf = PF_INET6;
	nfho_ipv6_in.priority = NF_IP6_PRI_FIRST;
	nf_register_net_hook(&init_net, &nfho_ipv6_in);

	nfho_ipv6_out.hook = ipv6_out_hook;
	nfho_ipv6_out.hooknum = NF_INET_LOCAL_OUT;
	nfho_ipv6_out.pf = PF_INET6;
	nfho_ipv6_out.priority = NF_IP6_PRI_FIRST;
	nf_register_net_hook(&init_net, &nfho_ipv6_out);

	//initialize hashmaps
	map_init(&rules.in_tcp_ports);
	map_init(&rules.out_tcp_ports);
	map_init(&rules.in_udp_ports);
	map_init(&rules.out_udp_ports);
	map_init(&rules.in_ipv4);
	map_init(&rules.out_ipv4);
	map_init(&rules.in_ipv6);
	map_init(&rules.out_ipv6);

	return 0;
}


//   Called when the module is removed/unloaded
void cleanup_module(){

	device_destroy(netblockcharClass, MKDEV(majorNumber, 0));
   	class_unregister(netblockcharClass);
   	class_destroy(netblockcharClass);
   	unregister_chrdev(majorNumber, DEVICE_NAME);
   	printk(KERN_INFO "netblock: unregistering netblock character device\n");

	map_deinit(&rules.in_tcp_ports);
	map_deinit(&rules.out_tcp_ports);
	map_deinit(&rules.in_udp_ports);
	map_deinit(&rules.out_udp_ports);
	map_deinit(&rules.in_ipv4);
	map_deinit(&rules.out_ipv4);
	map_deinit(&rules.in_ipv6);
	map_deinit(&rules.out_ipv6);
	nf_unregister_net_hook(&init_net, &nfho_ipv4_in);
	nf_unregister_net_hook(&init_net, &nfho_ipv4_out);
	nf_unregister_net_hook(&init_net, &nfho_ipv6_in);
	nf_unregister_net_hook(&init_net, &nfho_ipv6_out);
}

static int device_open(struct inode *inodep, struct file *filep){
   	printk(KERN_INFO "netblock: character device successfully opened\n");
   	return 0;
}

/*
	Commands are read in as strings:
		[command:1bit] [direction:1bit] [protocol:2bits] <value>

	1st Bit: (unblock=0, block=1)
	2nd Bit: (outgoing=0, incoming=1)
	3rd & 4th bit: (ipv4=0,ipv6=1,tcp=2,udp=3)

	Examples:
		"block outgoing udp 122" ===> 1101 = 13
		(Therefore, execute command #13 with value 122.)

		"unblock incoming ipv4 192.168.0.2" ===> 0010 = 2
		"unblock outgoing tcp 80" ===> 1000 = 8
*/

static ssize_t device_write(struct file *filep, const char *buffer, size_t len, loff_t *offset){

	char* cursor;
	char* token;
	unsigned char rule;
	int count;
   	snprintf(message, 255,"%s", buffer);

	//Parse the incoming rule
	cursor = &message[0];
	rule = 0;
	count = 0;
	while(cursor != NULL){
		count++;
		token = strsep(&cursor," ");
		if(strcmp(token, UNBLOCK) == 0){
			//do nothing
		}else if(strcmp(token, BLOCK) == 0){
			rule = rule | 0x1;
		}else if(strcmp(token, OUTGOING) == 0){
			//do nothing
		}else if(strcmp(token, INCOMING) == 0){
			rule = rule | 0x2;
		}else if(strcmp(token, IPV4) == 0){
			//do nothing
		}else if(strcmp(token, IPV6) == 0){
			rule = rule | 0x4;
		}else if(strcmp(token, TCP) == 0){
			rule = rule | 0x8;
		}else if(strcmp(token, UDP) == 0){
			rule = rule | 0xC;
		}else{
			if(cursor != NULL){
				printk(KERN_INFO "Invalid command sent to netblock module\n");
				return -1;
			}
		}
	}

	if(count != 4){
		printk(KERN_INFO "netblock: incorrectly formatted command\n");
		return -1;
	}

	//Apply action to ruleset
	switch(rule){
		case UNBLOCK_OUTGOING_IPV4_IP:
			map_remove(&rules.out_ipv4, token);
			break;
		case BLOCK_OUTGOING_IPV4_IP:
			map_set(&rules.out_ipv4, token, 0);
			break;
		case UNBLOCK_INCOMING_IPV4_IP:
			map_remove(&rules.in_ipv4, token);
			break;
		case BLOCK_INCOMING_IPV4_IP:
			map_set(&rules.in_ipv4, token, 0);
			break;
		case UNBLOCK_OUTGOING_IPV6_IP:
			map_remove(&rules.out_ipv6, token);
			break;
		case BLOCK_OUTGOING_IPV6_IP:
			map_set(&rules.out_ipv6, token, 0);
			break;
		case UNBLOCK_INCOMING_IPV6_IP:
			map_remove(&rules.in_ipv6, token);
			break;
		case BLOCK_INCOMING_IPV6_IP:
			map_set(&rules.in_ipv6, token, 0);
			break;
		case UNBLOCK_OUTGOING_TCP_PORT:
			map_remove(&rules.out_tcp_ports, token);
			break;
		case BLOCK_OUTGOING_TCP_PORT:
			map_set(&rules.out_tcp_ports, token, 0);
			break;
		case UNBLOCK_INCOMING_TCP_PORT:
			map_remove(&rules.in_tcp_ports, token);
			break;
		case BLOCK_INCOMING_TCP_PORT:
			map_set(&rules.in_tcp_ports, token, 0);
			break;
		case UNBLOCK_OUTGOING_UDP_PORT:
			map_remove(&rules.out_udp_ports, token);
			break;
		case BLOCK_OUTGOING_UDP_PORT:
			map_set(&rules.out_udp_ports, token, 0);
			break;
		case UNBLOCK_INCOMING_UDP_PORT:
			map_remove(&rules.in_udp_ports, token);
			break;
		case BLOCK_INCOMING_UDP_PORT:
			map_set(&rules.in_udp_ports, token, 0);
			break;
		default:
			printk(KERN_INFO "netblock: received invalid command\n");
			return -1;
	}

	printk(KERN_INFO "Peformed action %d on %s\n", rule, token);

   	return len;
}

static ssize_t device_read(struct file *filep, char *buffer, size_t len, loff_t *offset){
	int error_count = 0;
   	// copy_to_user has the format ( * to, *from, size) and returns 0 on success
   	error_count = copy_to_user(buffer, "Hello World", 11);

   	if (error_count==0){
      		printk(KERN_INFO "netblock: Sent %d characters to the user\n", 11);
      		return 0;
   	}else {
      		printk(KERN_INFO "netblock: Failed to send %d characters to the user\n", error_count);
      		return -EFAULT;
   	}
}

static int device_release(struct inode *inodep, struct file *filep){
   	printk(KERN_INFO "netblock: character device successfully closed\n");
   	return 0;
}
