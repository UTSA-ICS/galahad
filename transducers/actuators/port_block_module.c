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
#include <linux/kthread.h>
#include "map.h"

//netfilter hook options
static struct nf_hook_ops nfho;

//Unix Domain Socket Kernel Thread
static struct task_struct *uds_thread;

//function for printing IPv4 addresses
void printIP(unsigned int addr){
	unsigned char bytes[4];
	bytes[0] = addr & 0xFF;
	bytes[1] = (addr >> 8) & 0xFF;
	bytes[2] = (addr >> 16) & 0xFF;
	bytes[3] = (addr >> 24) & 0xFF;
	printk("%d.%d.%d.%d\n", bytes[3],bytes[2],bytes[1],bytes[0]);
}


//Convert an IP address into a decimal value
//Will change later... using for testing
unsigned int decimalIP(unsigned int a, unsigned int b, unsigned int c, unsigned int d){
	unsigned int ip;
	ip = 0;
	ip = (a << 24) + (b << 16) + (c << 8) + d;
	return ip;
}


//Unix Domain Socket Thread
int uds_func(void *data){
	while(!kthread_should_stop()){
		printk(KERN_INFO "Running UDS thread...");
		msleep(5000);
	}

	return 0;
}


//Function called when init_module conditions are met
unsigned int port_blocker_hook(void* priv, struct sk_buff *skb, const struct nf_hook_state *state){

	struct iphdr* ip_header;
	struct tcphdr* tcp_header;
	unsigned int dst_addr;
	unsigned int src_addr;
	unsigned int ip;
	uint16_t dst_port;
	uint16_t src_port;

	if(!skb){
		return NF_ACCEPT;
	}


	ip_header = ip_hdr(skb);
	if(!ip_header){
		return NF_ACCEPT;
	}

	//retrieve source and destination ports for the packet
	dst_addr = ntohl(ip_header->daddr);
	src_addr = ntohl(ip_header->saddr);


	printk(KERN_INFO "Destination address: ");
	printIP(dst_addr);
	printk(KERN_INFO "Source address: ");
	printIP(src_addr);

	//Test for blocking all traffic from an IP
	//IP Address (Google Server): 216.58.219.206
	ip = decimalIP(216,58,219,206);
	if(ip == 3627736014){
		printk(KERN_INFO "Blocking IP Address...\n");
		return NF_DROP;
	}

	if (ip_header->protocol == IPPROTO_TCP){

		tcp_header = (struct tcphdr*)((__u32*)ip_header + ip_header->ihl);
		if(!tcp_header){
			return NF_ACCEPT;
		}

		dst_port = ntohs(tcp_header->dest);
		src_port = ntohs(tcp_header->source);

		printk(KERN_INFO "Source Port: %u\n", src_port);
		printk(KERN_INFO "Dest port: %u\n", dst_port);

		//test for blocking all traffic incoming on port 80
		if(dst_port == 80){
			printk(KERN_INFO "dropping all port 80 packets\n");
			return NF_DROP;
		}
	}

	return NF_ACCEPT;
}



//Called when the module is loaded
int init_module(){

	printk(KERN_INFO "Loading port blocker module");
	//Set up Netfilter hook
	nfho.hook = port_blocker_hook;
	nfho.hooknum = NF_INET_PRE_ROUTING;
	nfho.pf = PF_INET;
	nfho.priority = NF_IP_PRI_FIRST;
	nf_register_net_hook(&init_net, &nfho);

	//start Unix Domain Socket thread
	char udsthrd[14] = "portblock_uds";
	uds_thread = kthread_run(uds_func, NULL, udsthrd);

	map_int_t m;
	map_init(&m);
	//map_set(&m, "testkey", 123);
	//int *val = map_get(&m, "testkey");
	//printk(KERN_INFO "Got value %d\n", *val);
	return 0;
}


//Called when the module is removed/unloaded
void cleanup_module(){
	kthread_stop(uds_thread);
	nf_unregister_net_hook(&init_net, &nfho);
}

